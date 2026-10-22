package faersight.showcasefp;

import java.io.*;
import java.nio.charset.StandardCharsets;
import java.nio.file.*;
import java.util.*;
import weka.associations.*;
import weka.core.*;

/** Pinned FPGrowth audit/export only; no changes to either frozen bridge. */
public final class ShowcaseFPGrowth {
    private static final class Audit extends FPGrowth {
        @Override protected ArrayList<BinaryItem> getSingletons(Object data) throws Exception {
            ArrayList<BinaryItem> result = super.getSingletons(data);
            ((CountedInstances)data).reads = 0;
            return result;
        }
        int internalRules() { return m_rules.size(); }
        int patterns() { return m_largeItemSets.size(); }
        int maximumLength() {
            int max = 0;
            for (Iterator<FrequentBinaryItemSet> it = m_largeItemSets.iterator(); it.hasNext();)
                max = Math.max(max, it.next().getItems().size());
            return max;
        }
    }
    /** Read-only observation: after singletons, each FP-tree cycle scans N rows. */
    private static final class CountedInstances extends Instances {
        long reads;
        CountedInstances(Reader reader) throws IOException { super(reader); }
        @Override public Instance instance(int i) { reads++; return super.instance(i); }
    }
    private static String json(Object value) {
        if (value == null) return "null";
        if (value instanceof Boolean || value instanceof Number) return value.toString();
        if (value instanceof Map<?,?>) {
            List<String> parts = new ArrayList<>();
            for (Map.Entry<?,?> e : ((Map<?,?>)value).entrySet())
                parts.add(json(e.getKey().toString()) + ":" + json(e.getValue()));
            return "{" + String.join(",", parts) + "}";
        }
        if (value instanceof Collection<?>) {
            List<String> parts = new ArrayList<>();
            for (Object item : (Collection<?>)value) parts.add(json(item));
            return "[" + String.join(",", parts) + "]";
        }
        StringBuilder result = new StringBuilder("\"");
        for (char c : value.toString().toCharArray()) {
            if (c == '\\' || c == '"') result.append('\\').append(c);
            else if (c < 32) result.append(String.format(Locale.ROOT, "\\u%04x", (int)c));
            else result.append(c);
        }
        return result.append('"').toString();
    }
    private static void writeJson(Path path, Object value) throws IOException {
        Files.writeString(path, json(value) + "\n", StandardCharsets.UTF_8);
    }
    private static List<String> items(Collection<Item> source) {
        List<String> names = new ArrayList<>();
        for (Item item : source) {
            if (!(item instanceof NominalItem) || ((NominalItem)item).getValueIndex() != 1)
                throw new IllegalStateException("Non-presence item: " + item);
            names.add(item.getAttribute().name() + "=1");
        }
        Collections.sort(names);
        if (names.isEmpty() || new HashSet<>(names).size() != names.size())
            throw new IllegalStateException("Empty/duplicate itemset");
        return names;
    }
    private static void csv(PrintWriter writer, Object... cells) {
        for (int i = 0; i < cells.length; i++) {
            if (i > 0) writer.print(',');
            writer.print("\"" + cells[i].toString().replace("\"", "\"\"") + "\"");
        }
        writer.print('\n');
    }
    public static void main(String[] args) throws Exception {
        if (!Version.VERSION.equals("3.8.6")) throw new IllegalStateException("Wrong WEKA");
        Path output = Path.of(args[1]);
        int expectedN = Integer.parseInt(args[2]), expectedA = Integer.parseInt(args[3]);
        boolean export = Boolean.parseBoolean(args[4]);
        Audit a = new Audit();
        String[] opts = Arrays.copyOfRange(args, 5, args.length);
        a.setOptions(opts);
        Utils.checkForRemainingOptions(opts);
        Map<String,Object> settings = new LinkedHashMap<>();
        settings.put("options", Arrays.asList(a.getOptions()));
        settings.put("find_all", a.getFindAllRulesForSupportLevel());
        settings.put("requested_rules", a.getNumRulesToFind());
        settings.put("positive_index", a.getPositiveIndex());
        settings.put("maximum_items", a.getMaxNumberOfItems());
        settings.put("upper", a.getUpperBoundMinSupport());
        settings.put("lower", a.getLowerBoundMinSupport());
        settings.put("delta", a.getDelta());
        settings.put("minimum_metric", a.getMinMetric());
        settings.put("metric_id", a.getMetricType().getSelectedTag().getID());
        settings.put("transactions_filter", a.getTransactionsMustContain());
        settings.put("rules_filter", a.getRulesMustContain());
        settings.put("available_processors", Runtime.getRuntime().availableProcessors());
        settings.put("max_heap_bytes", Runtime.getRuntime().maxMemory());
        writeJson(output.resolve("resolved_options.json"), settings);
        CountedInstances data;
        long loadStarted = System.nanoTime();
        try (BufferedReader reader = Files.newBufferedReader(Path.of(args[0]), StandardCharsets.UTF_8)) {
            data = new CountedInstances(reader);
        }
        if (data.numInstances() != expectedN || data.numAttributes() != expectedA
                || data.classIndex() != -1) throw new IllegalStateException("Input dimensions");
        Set<String> attributes = new HashSet<>();
        for (int i = 0; i < data.numAttributes(); i++) {
            Attribute att = data.attribute(i);
            if (!att.isNominal() || att.numValues() != 2 || !att.value(0).equals("0")
                    || !att.value(1).equals("1") || !attributes.add(att.name()))
                throw new IllegalStateException("Expected nominal {0,1}");
        }
        int empty = 0;
        for (Instance row : data) {
            if (row.weight() != 1) throw new IllegalStateException("Weighted row");
            boolean present = false;
            for (int i = 0; i < row.numValues(); i++) {
                double v = row.valueSparse(i);
                if (v != 0 && v != 1) throw new IllegalStateException("Missing/nonbinary");
                present |= v == 1;
            }
            if (!present) empty++;
        }
        double loadSeconds = (System.nanoTime() - loadStarted) / 1e9;
        long start = System.nanoTime();
        a.buildAssociations(data);
        double buildSeconds = (System.nanoTime() - start) / 1e9;
        List<AssociationRule> rules = a.getAssociationRules().getRules();
        Map<String,Object> result = new LinkedHashMap<>();
        result.put("weka_version", Version.VERSION);
        result.put("rows", data.numInstances());
        result.put("attributes", data.numAttributes());
        result.put("empty_transactions", empty);
        result.put("tree_build_passes", data.reads / data.numInstances());
        result.put("tree_row_reads", data.reads);
        result.put("resolved_lower_count", (int)Math.ceil(a.getLowerBoundMinSupport()*data.numInstances()));
        result.put("internal_qualifying_rules", a.internalRules());
        result.put("returned_rules", rules.size());
        result.put("api_equals_internal_count", rules.size() == a.internalRules());
        result.put("rule_policy_limit_reached", a.internalRules() >= a.getNumRulesToFind());
        result.put("frequent_itemsets", a.patterns());
        result.put("maximum_frequent_itemset_length", a.maximumLength());
        result.put("association_build_seconds", buildSeconds);
        result.put("load_validation_seconds", loadSeconds);
        result.put("settings", settings);
        boolean zero = rules.stream().anyMatch(r ->
            r.getPremise().stream().anyMatch(i -> ((NominalItem)i).getValueIndex() != 1) ||
            r.getConsequence().stream().anyMatch(i -> ((NominalItem)i).getValueIndex() != 1));
        result.put("has_nonpresence_items", zero);
        writeJson(output.resolve("run.json"), result);
        // Native full model text is retained, even for fixture modes that clip the API.
        Files.writeString(output.resolve("fpgrowth_raw.txt"), a.toString(), StandardCharsets.UTF_8);
        if (!export) return;
        if (zero) throw new IllegalStateException("Absence rules rejected");
        List<List<Object>> rows = new ArrayList<>();
        int rank = 0;
        for (AssociationRule rule : rules) {
            List<String> lhs = items(rule.getPremise()), rhs = items(rule.getConsequence());
            if (!Collections.disjoint(lhs, rhs)) throw new IllegalStateException("Overlapping sides");
            rows.add(Arrays.asList(json(lhs), json(rhs), lhs.size(), rhs.size(),
                rule.getTotalSupport(), rule.getPremiseSupport(), rule.getConsequenceSupport(),
                rule.getTotalTransactions(), (double)rule.getTotalSupport()/rule.getTotalTransactions(),
                rule.getNamedMetricValue("Confidence"), rule.getNamedMetricValue("Lift"),
                rule.getNamedMetricValue("Leverage"), rule.getNamedMetricValue("Conviction"),
                rule.getPrimaryMetricName(), rule.getPrimaryMetricValue(), ++rank,
                a.getLowerBoundMinSupport(), a.getMinMetric(), a.getNumRulesToFind(),
                Utils.joinOptions(a.getOptions())));
        }
        rows.sort(Comparator.comparing((List<Object> r) -> r.get(0).toString())
                .thenComparing(r -> r.get(1).toString()));
        try (PrintWriter writer = new PrintWriter(Files.newBufferedWriter(output.resolve("rules.csv"),
                StandardCharsets.UTF_8))) {
            csv(writer, "antecedent", "consequent", "antecedent_items", "consequent_items",
                "joint_count", "antecedent_count", "consequent_count", "n", "support", "confidence",
                "lift", "leverage", "conviction", "ranking_metric", "ranking_value", "weka_rank",
                "requested_support", "minimum_metric", "rule_cap", "resolved_options");
            for (List<Object> row : rows) csv(writer, row.toArray());
        }
        Files.writeString(output.resolve("complete.txt"), "weka=3.8.6\n");
    }
}
