package faersight;

import java.io.*;
import java.nio.charset.StandardCharsets;
import java.nio.file.*;
import java.util.*;
import java.util.regex.*;
import weka.associations.*;
import weka.core.*;

/** Actual WEKA Apriori search; all observations remain unweighted case reports. */
public final class WekaExperiment {
    private static final Pattern SUPPORT = Pattern.compile(
        "Minimum support:.*?\\((\\d+) instances\\)");

    private static final class AuditedApriori extends Apriori {
        int cycles() { return m_cycles; }
    }

    private static PrintWriter writer(Path path) throws IOException {
        return new PrintWriter(Files.newBufferedWriter(path, StandardCharsets.UTF_8));
    }

    private static void csv(PrintWriter out, Object... cells) {
        for (int i = 0; i < cells.length; i++) {
            if (i > 0) out.print(",");
            out.print("\"" + String.valueOf(cells[i]).replace("\"", "\"\"") + "\"");
        }
        out.print("\n");
    }

    private static double metric(AssociationRule rule, String wanted) throws Exception {
        String[] names = rule.getMetricNamesForRule();
        double[] values = rule.getMetricValuesForRule();
        for (int i = 0; i < names.length; i++) {
            if (names[i].equalsIgnoreCase(wanted)) return values[i];
        }
        throw new IllegalStateException("WEKA did not return metric " + wanted);
    }

    private static void checkItems(Collection<Item> items) {
        for (Item item : items) {
            if (!(item instanceof NominalItem) || ((NominalItem)item).getValueIndex() != 1) {
                throw new IllegalStateException("Absence/malformed item in raw WEKA rules: " + item);
            }
        }
    }

    private static void mine(Instances data, Path output, String projection, double support,
                             double minLift, int maxRules, PrintWriter rules,
                             PrintWriter runs) throws Exception {
        AuditedApriori apriori = new AuditedApriori();
        apriori.setNumRules(maxRules);
        apriori.setMetricType(new SelectedTag(1, Apriori.TAGS_SELECTION));
        apriori.setMinMetric(minLift);
        // In WEKA 3.8.6 -U also prunes high-support rules. Keep it at one.
        apriori.setUpperBoundMinSupport(1.0);
        apriori.setLowerBoundMinSupport(support);
        // buildAssociations starts at max(1-delta, lower), hence exactly lower.
        apriori.setDelta(1.0);
        apriori.setTreatZeroAsMissing(true);
        long started = System.nanoTime();
        apriori.buildAssociations(data);
        String raw = apriori.toString();
        Path rawDir = output.resolve("raw").resolve(Double.toString(support));
        Files.createDirectories(rawDir);
        Files.writeString(rawDir.resolve(projection + ".log"), raw, StandardCharsets.UTF_8);
        Matcher minimum = SUPPORT.matcher(raw);
        // Pinned 3.8.6 findLargeItemSets uses int(minSupport*N + 0.5).
        // toString omits support entirely when no large pair itemsets survive.
        int minimumCount = (int)(Math.max(support, 1.0/data.numInstances())
            * data.numInstances() + 0.5);
        boolean reported = minimum.find();
        if (reported && Integer.parseInt(minimum.group(1)) != minimumCount) {
            throw new IllegalStateException("WEKA support display/state disagreement");
        }
        List<AssociationRule> found = apriori.getAssociationRules().getRules();
        if (apriori.cycles() != 1 || (!reported && (!found.isEmpty() ||
                !raw.contains("No large itemsets and rules found!")))) {
            throw new IllegalStateException("Unexpected support schedule or raw output");
        }
        csv(runs, projection, support, data.numInstances(), data.numAttributes(),
            minimumCount, found.size(), found.size() >= maxRules,
            apriori.cycles(), reported ? "raw_output_verified" : "pinned_3.8.6_rounding_no_itemsets",
            Utils.joinOptions(apriori.getOptions()), (System.nanoTime()-started)/1e9);
        runs.flush();
        int rank = 0;
        for (AssociationRule rule : found) {
            rank++;
            checkItems(rule.getPremise());
            checkItems(rule.getConsequence());
            if (rule.getPremise().size() != 1 || rule.getConsequence().size() != 1) continue;
            Item lhs = rule.getPremise().iterator().next();
            Item rhs = rule.getConsequence().iterator().next();
            String left = lhs.getAttribute().name();
            String right = rhs.getAttribute().name();
            if (!left.startsWith("DRUG_") || !right.startsWith("REAC_")) continue;
            csv(rules, projection, support, rank, left.substring(5), right.substring(5),
                rule.getPremiseSupport(), rule.getConsequenceSupport(), rule.getTotalSupport(),
                rule.getTotalTransactions(), metric(rule,"Confidence"), metric(rule,"Lift"));
        }
        rules.flush();
    }

    public static void main(String[] args) throws Exception {
        if (args.length != 7) throw new IllegalArgumentException(
            "ARFF OUTPUT SUPPORTS MIN_LIFT MAX_RULES EXPECTED_N projected|full");
        if (!Version.VERSION.equals("3.8.6")) throw new IllegalStateException("Expected WEKA 3.8.6");
        Path output = Path.of(args[1]);
        Files.createDirectories(output);
        Instances base;
        try (BufferedReader reader = Files.newBufferedReader(Path.of(args[0]), StandardCharsets.UTF_8)) {
            base = new Instances(reader);
        }
        if (base.numInstances() != Integer.parseInt(args[5])) {
            throw new IllegalStateException("ARFF report population changed");
        }
        List<Integer> drugs = new ArrayList<>(), reactions = new ArrayList<>();
        for (int j = 0; j < base.numAttributes(); j++) {
            Attribute attribute = base.attribute(j);
            if (!attribute.isNominal() || attribute.numValues() != 2 ||
                    !attribute.value(0).equals("0") || !attribute.value(1).equals("1")) {
                throw new IllegalStateException("Attributes must be nominal {0,1}");
            }
            if (attribute.name().startsWith("DRUG_")) drugs.add(j);
            else if (attribute.name().startsWith("REAC_")) reactions.add(j);
            else throw new IllegalStateException("Unknown item namespace");
        }
        if (drugs.isEmpty() || reactions.isEmpty()) throw new IllegalStateException("Missing namespaces");
        int[][] drugPresence = new int[base.numInstances()][];
        for (int i = 0; i < base.numInstances(); i++) {
            Instance instance = base.instance(i);
            if (instance.weight() != 1.0) throw new IllegalStateException("Weighted reports not allowed");
            for (int k = 0; k < instance.numValues(); k++) {
                double value = instance.valueSparse(k);
                if (value != 0.0 && value != 1.0) throw new IllegalStateException("Missing/nonbinary value");
            }
            int[] temporary = new int[drugs.size()];
            int count = 0;
            for (int j = 0; j < drugs.size(); j++) {
                if (instance.value(drugs.get(j)) == 1.0) temporary[count++] = j;
            }
            drugPresence[i] = Arrays.copyOf(temporary, count);
        }
        double[] supports = Arrays.stream(args[2].split(",")).mapToDouble(Double::parseDouble).toArray();
        double minLift = Double.parseDouble(args[3]);
        int cap = Integer.parseInt(args[4]);
        try (PrintWriter rules = writer(output.resolve("weka_rules.csv"));
             PrintWriter runs = writer(output.resolve("weka_runs.csv"))) {
            csv(rules,"projection","support_requested","projection_rank","drug","reaction",
                "drug_count","reaction_count","joint_count","n","weka_confidence","weka_lift");
            csv(runs,"projection","support_requested","n","attributes","min_support_count",
                "all_rules","cap_reached","cycles","support_count_source","options","seconds");
            if (args[6].equals("full")) {
                for (double support : supports) mine(base,output,"full",support,minLift,cap,rules,runs);
            } else if (args[6].equals("projected")) {
                for (int r = 0; r < reactions.size(); r++) {
                    ArrayList<Attribute> attributes = new ArrayList<>();
                    for (int d : drugs) attributes.add(new Attribute(base.attribute(d).name(),
                        new ArrayList<>(Arrays.asList("0","1"))));
                    attributes.add(new Attribute(base.attribute(reactions.get(r)).name(),
                        new ArrayList<>(Arrays.asList("0","1"))));
                    Instances projected = new Instances("faersight_projection", attributes, base.numInstances());
                    for (int i = 0; i < base.numInstances(); i++) {
                        boolean event = base.instance(i).value(reactions.get(r)) == 1.0;
                        int[] indices = Arrays.copyOf(drugPresence[i], drugPresence[i].length + (event ? 1 : 0));
                        if (event) indices[indices.length-1] = drugs.size();
                        double[] values = new double[indices.length];
                        Arrays.fill(values,1.0);
                        projected.add(new SparseInstance(1.0,values,indices,attributes.size()));
                    }
                    String name = String.format(Locale.ROOT,"r%04d",r);
                    for (double support : supports) mine(projected,output,name,support,minLift,cap,rules,runs);
                    System.out.println("Completed reaction " + (r+1) + "/" + reactions.size());
                }
            } else throw new IllegalArgumentException("Unknown execution mode");
        }
        Files.writeString(output.resolve("complete.txt"),
            "weka="+Version.VERSION+"\nn="+base.numInstances()+"\nattributes="+base.numAttributes()+"\n",
            StandardCharsets.UTF_8);
    }
}
