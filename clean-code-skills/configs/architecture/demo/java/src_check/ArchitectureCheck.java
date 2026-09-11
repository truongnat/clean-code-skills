import com.tngtech.archunit.core.domain.JavaClasses;
import com.tngtech.archunit.core.importer.ClassFileImporter;
import com.tngtech.archunit.core.importer.ImportOption;
import com.tngtech.archunit.lang.ArchRule;
import com.tngtech.archunit.lang.syntax.ArchRuleDefinition;
import com.tngtech.archunit.library.Architectures;

/**
 * The Java half of arch-scan: ArchUnit reads real bytecode, so this is the strict version
 * of the same three rules the shell CI runs for other languages.
 *
 *   javac -cp archunit.jar:slf4j-api.jar -d classes $(find src src_check -name '*.java')
 *   java  -cp classes:archunit.jar:slf4j-api.jar ArchitectureCheck   # exit 1 on violation
 *
 * In a Maven/Gradle build, drop the main() and annotate the rules with @AnalyzeClasses +
 * @ArchTest instead - same rules, reported as test failures.
 */
public final class ArchitectureCheck {

    private static final String ROOT = "com.example";

    public static void main(String[] args) {
        JavaClasses classes = new ClassFileImporter()
                .withImportOption(new ImportOption.DoNotIncludeTests())
                .importPackages(ROOT);

        int failures = 0;
        failures += check(layered(), classes, "layers point inward");
        failures += check(noDriversInDomain(), classes, "domain is framework-free");
        failures += check(noCycles(), classes, "no package cycles");
        if (failures > 0) {
            System.out.println("Architecture check: " + failures + " rule(s) broken.");
            System.exit(1);
        }
        System.out.println("Architecture check: all 3 rules kept.");
    }

    private static int check(ArchRule rule, JavaClasses classes, String label) {
        try {
            rule.check(classes);
            System.out.println("  KEPT   " + label);
            return 0;
        } catch (AssertionError failure) {
            System.out.println("  BROKEN " + label);
            System.out.println(indent(firstLines(failure.getMessage(), 6)));
            return 1;
        }
    }

    private static ArchRule layered() {
        return Architectures.layeredArchitecture().consideringOnlyDependenciesInLayers()
                .layer("Domain").definedBy("..domain..")
                .layer("Application").definedBy("..application..")
                .layer("Infrastructure").definedBy("..infrastructure..")
                .layer("Interfaces").definedBy("..interfaces..")
                .whereLayer("Domain").mayOnlyBeAccessedByLayers("Application", "Infrastructure", "Interfaces")
                .whereLayer("Application").mayOnlyBeAccessedByLayers("Interfaces", "Infrastructure")
                .whereLayer("Infrastructure").mayOnlyBeAccessedByLayers("Interfaces");
    }

    private static ArchRule noDriversInDomain() {
        return ArchRuleDefinition.noClasses().that().resideInAPackage("..domain..")
                .should().dependOnClassesThat().resideInAnyPackage(
                        "java.sql..", "javax.persistence..", "org.springframework..", "org.hibernate..")
                .because("the domain must be testable without a driver or a framework");
    }

    private static ArchRule noCycles() {
        return com.tngtech.archunit.library.dependencies.SlicesRuleDefinition.slices()
                .matching(ROOT + ".(*)..").should().beFreeOfCycles();
    }

    private static String firstLines(String message, int limit) {
        String[] lines = message == null ? new String[0] : message.split("\n");
        return String.join("\n", java.util.Arrays.copyOf(lines, Math.min(limit, lines.length)));
    }

    private static String indent(String text) {
        return "         " + text.replace("\n", "\n         ");
    }

    private ArchitectureCheck() {
    }
}
