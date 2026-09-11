# ArchUnit demo (Java) — verified with real bytecode

Same three rules as `arch-scan`, enforced where Java belongs: in the build, against compiled
classes. ArchUnit 1.3.0 + OpenJDK 11, no Maven or Gradle needed for the demo.

Get the two JARs first (not vendored in this repo - they are third-party binaries):

    mkdir -p javalib && cd javalib
    curl -sLO https://repo1.maven.org/maven2/com/tngtech/archunit/archunit/1.3.0/archunit-1.3.0.jar
    curl -sLO https://repo1.maven.org/maven2/org/slf4j/slf4j-api/2.0.13/slf4j-api-2.0.13.jar
    cd -

Then:

    cd configs/architecture/demo/java
    CP=../../../../javalib/archunit-1.3.0.jar:../../../../javalib/slf4j-api-2.0.13.jar
    javac -nowarn -cp $CP -d classes $(find src src_check -name '*.java')
    java -cp classes:$CP ArchitectureCheck          # exit 1 on violation

Measured here (JDK 11, archunit-1.3.0 + slf4j-api-2.0.13):

| State of `src/com/example/domain/LegacyTotal.java` | Output | Exit |
|---|---|---|
| present (imports `java.sql.Connection` + `com.example.infrastructure.OrderRepository`) | `BROKEN layers point inward` · `BROKEN domain is framework-free` · `BROKEN no package cycles` | 1 |
| deleted | `KEPT` for all 3 — `Architecture check: all 3 rules kept.` | 0 |

The `SLF4J(W): No SLF4J providers were found` line is noise from the missing logger binding;
add `slf4j-simple` if it bothers you. It does not affect the result.

## In a real build

```xml
<dependency>
  <groupId>com.tngtech.archunit</groupId>
  <artifactId>archunit-junit5</artifactId>
  <version>1.3.0</version>
  <scope>test</scope>
</dependency>
```

Then keep the rules and drop the `main()`:

```java
@AnalyzeClasses(packages = "com.example", importOptions = ImportOption.DoNotIncludeTests.class)
class ArchitectureTest {
    @ArchTest
    static final ArchRule layersPointInward = ArchitectureCheck.layered();   // reuse the rule
}
```

Why both ArchUnit and `arch-scan`? ArchUnit is exact (bytecode) but only for JVM languages and
only after a compile; `arch-scan` is a heuristic but runs in 0.2 s on any language, pre-compile,
in a pre-commit hook. Same rule names, so a violation reads the same in both reports.
