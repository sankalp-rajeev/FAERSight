package faersight.metricstudy;

import java.util.Collections;
import weka.associations.AprioriItemSet;
import weka.associations.DefaultAssociationRule;
import weka.core.Version;

/** Evaluate count-only metric APIs. Never constructs or runs an associator. */
public class MetricProbe {
    public static void main(String[] args) throws Exception {
        if (!Version.VERSION.equals("3.8.6")) throw new IllegalStateException("Wrong WEKA");
        System.out.println("n,lhs,rhs,joint,confidence,lift,leverage,conviction,apriori_conviction");
        int[][] cases = {{20,5,7,5},{20,1,1,1},{20,20,20,20},{20,9,7,5}};
        for (int[] c : cases) {
            int n=c[0], lhs=c[1], rhs=c[2], joint=c[3];
            DefaultAssociationRule r = new DefaultAssociationRule(
                Collections.emptyList(), Collections.emptyList(),
                DefaultAssociationRule.METRIC_TYPE.LIFT, lhs,rhs,joint,n);
            AprioriItemSet left = new AprioriItemSet(n);
            AprioriItemSet both = new AprioriItemSet(n);
            left.setCounter(lhs);
            both.setCounter(joint);
            System.out.println(n+","+lhs+","+rhs+","+joint+","
                +r.getNamedMetricValue("Confidence")+","+r.getNamedMetricValue("Lift")+","
                +r.getNamedMetricValue("Leverage")+","+r.getNamedMetricValue("Conviction")+","
                +both.convictionForRule(left,both,lhs,rhs));
        }
    }
}
