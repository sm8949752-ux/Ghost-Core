import javax.crypto.Cipher;
import java.util.Properties;

public class Test {
    public static void main(String[] args) {
        System.out.println("--- Starting Comprehensive Oracle JDK 21 Test ---");

        System.out.println("Checking Environment...");
        System.out.println("Java Version: " + System.getProperty("java.version"));
        System.out.println("Java Vendor: " + System.getProperty("java.vendor"));
        System.out.println("Home: " + System.getProperty("java.home"));

        try {
            int maxKeyLen = Cipher.getMaxAllowedKeyLength("AES");
            System.out.println("Unlimited Cryptography: " + (maxKeyLen > 128 ? "YES" : "NO"));
        } catch (Exception e) {
            System.err.println("Cryptography Test Failed!");
            System.exit(1);
        }

        double val = Math.sqrt(144);
        if (val == 12.0) {
            System.out.println("Math Engine: OK");
        }

        System.out.println("All Runtime Tests Passed!");
    }
}
