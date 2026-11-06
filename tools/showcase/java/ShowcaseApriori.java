package faersight.showcase;

import java.io.*;
import java.lang.management.ManagementFactory;
import java.nio.charset.StandardCharsets;
import java.nio.file.*;
import java.util.*;
import weka.associations.*;
import weka.core.*;

/** Separate full-attribute exporter. It applies no drug/reaction direction filter. */
public final class ShowcaseApriori {
    private static final class Audit extends Apriori {
        int cycles() { return m_cycles; }
        double usedSupport() { return m_minSupport; }
        int maximumFrequentLength() {
            int maximum = 0;
            if (m_Ls != null) for (int i = 0; i < m_Ls.size(); i++) {
                if (!m_Ls.get(i).isEmpty()) maximum = i + 1;
            }
            return maximum;
        }
        long frequentItemsets() {
            long count = 0;
            if (m_Ls != null) for (ArrayList<Object> level : m_Ls) count += level.size();
            return count;
        }
    }

    private static String json(Object value) {
        if (value == null) return "null";
        if (value instanceof Boolean || value instanceof Number) return value.toString();
        if (value instanceof Map<?,?>) {
            List<String> parts = new ArrayList<>();
            for (Map.Entry<?,?> e : ((Map<?,?>) value).entrySet()) {
                parts.add(json(e.getKey().toString()) + ":" + json(e.getValue()));
            }
            return "{" + String.join(",", parts) + "}";
        }
        if (value instanceof Collection<?>) {
            List<String> parts = new ArrayList<>();
            for (Object item : (Collection<?>) value) parts.add(json(item));
            return "[" + String.join(",", parts) + "]";
        }
        String s = value.toString();
        StringBuilder result = new StringBuilder("\"");
        for (char c : s.toCharArray()) {
            if (c == '\\' || c == '"') result.append('\\').append(c);
            else if (c < 32) result.append(String.format(Locale.ROOT, "\\u%04x", (int)c));
            else result.append(c);
        }
        return result.append('"').toString();
    }

    private static void writeJson(Path path, Object value) throws IOException {
        Files.writeString(path, json(value) + "\n", StandardCharsets.UTF_8);
    }

    private static void csv(PrintWriter writer, Object... cells) {
        for (int i = 0; i < cells.length; i++) {
            if (i > 0) writer.print(',');
            writer.print("\"" + cells[i].toString().replace("\"", "\"\"") + "\"");
        }
        writer.print('\n');
    }

    private static List<String> items(Collection<Item> source) {
        List<String> names = new ArrayList<>();
        for (Item item : source) {
            if (!(item instanceof NominalItem) || ((NominalItem)item).getValueIndex() != 1) {
                throw new IllegalStateException("Absence-derived or unsupported item: " + item);
            }
            names.add(item.getAttribute().name() + "=1");
        }
        Collections.sort(names);
        if (names.isEmpty() || new HashSet<>(names).size() != names.size()) {
            throw new IllegalStateException("Empty or duplicated rule itemset");
        }
        return names;
    }

    private static Map<String,Object> settings(Apriori a) {
        Map<String,Object> map = new LinkedHashMap<>();
        map.put("options", Arrays.asList(a.getOptions()));
        map.put("metric_id", a.getMetricType().getSelectedTag().getID());
        map.put("minimum_metric", a.getMinMetric());
        map.put("requested_rules", a.getNumRules());
        map.put("upper_support", a.getUpperBoundMinSupport());
        map.put("lower_support", a.getLowerBoundMinSupport());
        map.put("delta", a.getDelta());
        map.put("significance_level", a.getSignificanceLevel());
        map.put("treat_zero_as_missing", a.getTreatZeroAsMissing());
        map.put("class_rules", a.getCar());
        map.put("class_index_option", a.getClassIndex());
        map.put("remove_all_missing_columns", a.getRemoveAllMissingCols());
        map.put("print_itemsets", a.getOutputItemSets());
        map.put("verbose", a.getVerbose());
        return map;
    }

    private static List<String> options(String support, String cap) {
        return Arrays.asList("-N", cap, "-T", "1", "-C", "1.2", "-D", "1.0",
                             "-U", "1.0", "-M", support, "-S", "-1.0", "-Z", "-c", "-1");
    }

    private static void inspect(Path output) throws Exception {
        Map<String,Object> audit = new LinkedHashMap<>();
        audit.put("weka_version", Version.VERSION);
        audit.put("java_version", System.getProperty("java.runtime.version"));
        audit.put("available_processors", Runtime.getRuntime().availableProcessors());
        audit.put("max_heap_bytes", Runtime.getRuntime().maxMemory());
        audit.put("jvm_arguments", ManagementFactory.getRuntimeMXBean().getInputArguments());
        audit.put("defaults", settings(new Apriori()));
        Map<String,Object> metrics = new LinkedHashMap<>();
        for (Tag tag : Apriori.TAGS_SELECTION) metrics.put(Integer.toString(tag.getID()), tag.getReadable());
        audit.put("metric_identifiers", metrics);
        List<Object> ladder = new ArrayList<>();
        for (String support : Arrays.asList("0.001", "0.0005", "0.0002", "0.0001")) {
            Apriori a = new Apriori();
            a.setOptions(options(support, "100000").toArray(new String[0]));
            Map<String,Object> run = settings(a);
            run.put("minimum_count_at_385288", (int)(Math.max(Double.parseDouble(support),
                1.0 / 385288) * 385288 + 0.5));
            ladder.add(run);
        }
        audit.put("resolved_ladder", ladder);
        audit.put("full_data_mining_started", false);
        writeJson(output.resolve("runtime_and_options.json"), audit);
    }

    private static void probes(Path fixture, Path output) throws Exception {
        Instances data;
        try (BufferedReader reader = Files.newBufferedReader(fixture, StandardCharsets.UTF_8)) {
            data = new Instances(reader);
        }
        if (data.numInstances() != 20 || data.numAttributes() != 4) {
            throw new IllegalArgumentException("Semantic probes accept the 20x4 fixture only");
        }
        List<Object> result = new ArrayList<>();
        for (String name : Arrays.asList("fixed", "default_delta", "upper_equals_lower", "without_Z")) {
            Audit a = new Audit();
            a.setOptions(options("0.1", "100000").toArray(new String[0]));
            if (name.equals("default_delta")) a.setDelta(0.05);
            if (name.equals("upper_equals_lower")) a.setUpperBoundMinSupport(0.1);
            if (name.equals("without_Z")) a.setTreatZeroAsMissing(false);
            a.buildAssociations(data);
            Map<String,Object> row = settings(a);
            row.put("probe", name);
            row.put("cycles", a.cycles());
            List<AssociationRule> rules = a.getAssociationRules().getRules();
            row.put("returned_rules", rules.size());
            row.put("has_zero_items", rules.stream().anyMatch(r ->
                r.getPremise().stream().anyMatch(i -> ((NominalItem)i).getValueIndex() == 0) ||
                r.getConsequence().stream().anyMatch(i -> ((NominalItem)i).getValueIndex() == 0)));
            result.add(row);
        }
        writeJson(output.resolve("semantic_probes.json"), result);
    }

    private static void mine(String[] args, Path output) throws Exception {
        int expectedN = Integer.parseInt(args[3]);
        int expectedAttributes = Integer.parseInt(args[4]);
        String[] requested = Arrays.copyOfRange(args, 5, args.length);
        Audit a = new Audit();
        String[] parsed = requested.clone();
        a.setOptions(parsed);
        Utils.checkForRemainingOptions(parsed);
        Map<String,Object> resolved = settings(a);
        writeJson(output.resolve("resolved_options.json"), resolved);
        if (a.getCar() || a.getRemoveAllMissingCols() || !a.getTreatZeroAsMissing()
            || a.getSignificanceLevel() != -1.0 || a.getMetricType().getSelectedTag().getID() != 1
            || a.getUpperBoundMinSupport() != 1.0 || a.getDelta() != 1.0) {
            throw new IllegalArgumentException("Non-registered showcase Apriori options");
        }
        long processStarted = System.nanoTime();
        Instances data;
        try (BufferedReader reader = Files.newBufferedReader(Path.of(args[1]), StandardCharsets.UTF_8)) {
            data = new Instances(reader);
        }
        if (data.numInstances() != expectedN || data.numAttributes() != expectedAttributes
            || data.classIndex() != -1) throw new IllegalStateException("Input dimensions/class changed");
        Set<String> attributes = new HashSet<>();
        for (int i = 0; i < data.numAttributes(); i++) {
            Attribute att = data.attribute(i);
            if (!att.isNominal() || att.numValues() != 2 || !att.value(0).equals("0")
                || !att.value(1).equals("1") || !attributes.add(att.name())) {
                throw new IllegalStateException("Expected unique nominal {0,1} attributes");
            }
        }
        int empty = 0;
        for (Instance row : data) {
            if (row.weight() != 1.0) throw new IllegalStateException("Weighted input");
            boolean present = false;
            for (int j = 0; j < row.numValues(); j++) {
                double v = row.valueSparse(j);
                if (v != 0.0 && v != 1.0) throw new IllegalStateException("Missing/nonbinary input");
                present |= v == 1.0;
            }
            if (!present) empty++;
        }
        long started = System.nanoTime();
        a.buildAssociations(data);
        double buildSeconds = (System.nanoTime() - started) / 1e9;
        Files.writeString(output.resolve("apriori_raw.txt"), a.toString(), StandardCharsets.UTF_8);
        List<AssociationRule> rules = a.getAssociationRules().getRules();
        Map<String,Object> result = new LinkedHashMap<>();
        result.put("weka_version", Version.VERSION);
        result.put("rows", data.numInstances());
        result.put("attributes", data.numAttributes());
        result.put("empty_transactions", empty);
        result.put("cycles", a.cycles());
        result.put("support_used", a.usedSupport());
        result.put("minimum_count", (int)(a.usedSupport() * data.numInstances() + 0.5));
        result.put("returned_rules", rules.size());
        result.put("rule_cap_reached_or_ambiguous", rules.size() >= a.getNumRules());
        result.put("maximum_frequent_itemset_length", a.maximumFrequentLength());
        result.put("frequent_itemsets", a.frequentItemsets());
        result.put("integer_partition_limit_exceeded", a.maximumFrequentLength() >= 31);
        result.put("association_build_seconds", buildSeconds);
        result.put("load_and_build_seconds", (System.nanoTime() - processStarted) / 1e9);
        result.put("settings", resolved);
        writeJson(output.resolve("run.json"), result);
        List<List<Object>> rows = new ArrayList<>();
        int rank = 0;
        for (AssociationRule rule : rules) {
            rank++;
            List<String> lhs = items(rule.getPremise()), rhs = items(rule.getConsequence());
            Set<String> intersection = new HashSet<>(lhs);
            intersection.retainAll(rhs);
            if (!intersection.isEmpty()) throw new IllegalStateException("Overlapping rule sides");
            rows.add(Arrays.asList(json(lhs), json(rhs), lhs.size(), rhs.size(),
                rule.getTotalSupport(), rule.getPremiseSupport(), rule.getConsequenceSupport(),
                rule.getTotalTransactions(), (double)rule.getTotalSupport() / rule.getTotalTransactions(),
                rule.getNamedMetricValue("Confidence"), rule.getNamedMetricValue("Lift"),
                rule.getNamedMetricValue("Leverage"), rule.getNamedMetricValue("Conviction"),
                rule.getPrimaryMetricName(), rule.getPrimaryMetricValue(), rank,
                a.getLowerBoundMinSupport(), a.getMinMetric(), a.getNumRules(),
                Utils.joinOptions(a.getOptions())));
        }
        rows.sort(Comparator.comparing((List<Object> r) -> r.get(0).toString())
                            .thenComparing(r -> r.get(1).toString()));
        try (PrintWriter writer = new PrintWriter(Files.newBufferedWriter(output.resolve("rules.csv"),
                StandardCharsets.UTF_8))) {
            csv(writer, "antecedent", "consequent", "antecedent_items", "consequent_items",
                "joint_count", "antecedent_count", "consequent_count", "n", "support",
                "confidence", "lift", "leverage", "conviction", "ranking_metric", "ranking_value",
                "weka_rank", "requested_support", "minimum_metric", "rule_cap", "resolved_options");
            for (List<Object> row : rows) csv(writer, row.toArray());
        }
        if (a.cycles() != 1) throw new IllegalStateException("Not a one-cycle fixed-support run");
        Files.writeString(output.resolve("complete.txt"), "weka=3.8.6\n", StandardCharsets.UTF_8);
    }

    public static void main(String[] args) throws Exception {
        if (!Version.VERSION.equals("3.8.6")) throw new IllegalStateException("Wrong WEKA version");
        if (args.length == 2 && args[0].equals("inspect")) {
            Path output = Path.of(args[1]);
            Files.createDirectories(output);
            inspect(output);
        } else if (args.length == 3 && args[0].equals("probes")) {
            Path output = Path.of(args[2]);
            Files.createDirectories(output);
            probes(Path.of(args[1]), output);
        } else if (args.length > 5 && args[0].equals("mine")) {
            Path output = Path.of(args[2]);
            Files.createDirectories(output);
            mine(args, output);
        } else throw new IllegalArgumentException("inspect OUTPUT | mine ARFF OUTPUT N ATTRIBUTES OPTIONS...");
    }
}
