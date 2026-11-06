package faersight.explorerdemo;

import java.beans.Introspector;
import java.beans.PropertyDescriptor;
import java.io.BufferedReader;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.ArrayList;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import weka.associations.Apriori;
import weka.associations.FPGrowth;
import weka.core.Instances;
import weka.core.OptionHandler;
import weka.core.SelectedTag;
import weka.core.Utils;
import weka.core.Version;

/** Parse a prepared projection and inspect beans. No GUI input or association build. */
public final class ExplorerPreflight {
    private static String json(Object value) {
        if (value == null) return "null";
        if (value instanceof Number || value instanceof Boolean) return value.toString();
        if (value instanceof Map<?,?>) {
            List<String> fields = new ArrayList<>();
            for (Map.Entry<?,?> e : ((Map<?,?>)value).entrySet())
                fields.add(json(e.getKey().toString())+":"+json(e.getValue()));
            return "{"+String.join(",",fields)+"}";
        }
        if (value instanceof Iterable<?>) {
            List<String> items = new ArrayList<>();
            for (Object item : (Iterable<?>)value) items.add(json(item));
            return "["+String.join(",",items)+"]";
        }
        return "\""+value.toString().replace("\\","\\\\").replace("\"","\\\"")
            .replace("\r","\\r").replace("\n","\\n").replace("\t","\\t")+"\"";
    }

    private static Map<String,Object> bean(OptionHandler algorithm, String options) throws Exception {
        algorithm.setOptions(Utils.splitOptions(options));
        Map<String,Object> info = new LinkedHashMap<>();
        info.put("class",algorithm.getClass().getName());
        info.put("resolved_options",Utils.joinOptions(algorithm.getOptions()));
        List<Object> properties = new ArrayList<>();
        for (PropertyDescriptor p : Introspector.getBeanInfo(algorithm.getClass()).getPropertyDescriptors()) {
            if (p.getReadMethod()==null || p.getWriteMethod()==null) continue;
            Map<String,Object> field = new LinkedHashMap<>();
            field.put("property",p.getName());
            field.put("display_name",p.getDisplayName());
            Object value = p.getReadMethod().invoke(algorithm);
            field.put("value",value instanceof Number || value instanceof Boolean ? value : String.valueOf(value));
            if (value instanceof SelectedTag) {
                field.put("tag_id",((SelectedTag)value).getSelectedTag().getID());
                field.put("tag_label",((SelectedTag)value).getSelectedTag().getReadable());
            }
            try { field.put("tip_text",algorithm.getClass().getMethod(p.getName()+"TipText").invoke(algorithm)); }
            catch (NoSuchMethodException e) { field.put("tip_text",null); }
            properties.add(field);
        }
        info.put("bean_properties",properties);
        info.put("GUI_observed",false);
        return info;
    }

    public static void main(String[] args) throws Exception {
        if (!Version.VERSION.equals("3.8.6")) throw new IllegalStateException("Wrong WEKA version");
        Map<String,Object> report = new LinkedHashMap<>();
        report.put("weka_version",Version.VERSION);
        report.put("java_version",System.getProperty("java.runtime.version"));
        report.put("max_heap_bytes",Runtime.getRuntime().maxMemory());
        report.put("available_processors",Runtime.getRuntime().availableProcessors());
        long started=System.nanoTime();
        Instances data;
        try (BufferedReader r=Files.newBufferedReader(Path.of(args[0]),StandardCharsets.UTF_8)) {
            data=new Instances(r);
        }
        report.put("API_parse_seconds_not_GUI_load_time",(System.nanoTime()-started)/1e9);
        report.put("rows",data.numInstances()); report.put("attributes",data.numAttributes());
        List<Object> counts=new ArrayList<>();
        int[] presence=new int[data.numAttributes()]; int empty=0;
        for(int j=0;j<data.numAttributes();j++) {
            if (!data.attribute(j).isNominal() || data.attribute(j).numValues()!=2
                || !data.attribute(j).value(0).equals("0") || !data.attribute(j).value(1).equals("1"))
                throw new IllegalStateException("Wrong nominal order");
        }
        for(int i=0;i<data.numInstances();i++) {
            boolean any=false;
            if(data.instance(i).weight()!=1.0) throw new IllegalStateException("Weighted report");
            for(int j=0;j<data.numAttributes();j++) {
                double v=data.instance(i).value(j);
                if(v!=0 && v!=1) throw new IllegalStateException("Nonbinary value");
                if(v==1) {presence[j]++;any=true;}
            }
            if(!any) empty++;
        }
        for(int j=0;j<presence.length;j++) {
            Map<String,Object> c=new LinkedHashMap<>();
            c.put("name",data.attribute(j).name());c.put("present",presence[j]);counts.add(c);
        }
        report.put("presence_counts",counts);report.put("empty_reports",empty);
        report.put("primary_apriori",bean(new Apriori(),args[2]));
        report.put("unrestricted_apriori",bean(new Apriori(),args[3]));
        report.put("unrestricted_fpgrowth",bean(new FPGrowth(),args[4]));
        report.put("association_builds",0);report.put("GUI_observed",false);
        Files.writeString(Path.of(args[1]),json(report)+"\n",StandardCharsets.UTF_8);
    }
}
