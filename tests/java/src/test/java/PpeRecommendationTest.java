// PpeRecommendationTest.java 
import static org.junit.jupiter.api.Assertions.assertTrue; 
import java.util.ArrayList; 
import java.util.List; 
import org.junit.jupiter.api.Test; 
 

class PpeRecommendationTest { 
 

    static List<String> recommendPpe(String hazardType, String severity, String exposureRoute) { 
        // MVP rule-based logic (replace with your real implementation) 
        List<String> recs = new ArrayList<>(); 
        if ("chemical".equals(hazardType)) { 
            recs.add("chemical-resistant gloves"); 
            recs.add("splash goggles"); 
        } 
        if (exposureRoute.contains("inhalation") || "high".equals(severity)) { 
            recs.add("respirator"); 
        } 
        return recs; 
    } 
 

    @Test 
    void chemicalHighInhalationIncludesRespirator() { 
        List<String> recs = recommendPpe("chemical", "high", "inhalation"); 
        assertTrue(recs.contains("respirator")); 
    } 
} 
 

 

 

 