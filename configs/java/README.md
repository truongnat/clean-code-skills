# JVM configuration (Checkstyle) for clean code

File: `checkstyle.xml` - verified to run on **Checkstyle 10.21.4**
(`CyclomaticComplexity`, `MagicNumber`, `MethodLength`, `ParameterNumber`,
`EmptyCatchBlock`, `NestedIfDepth` and `TodoComment` all fire on the demo file).

> When changing versions: some modules were removed or moved by Checkstyle
> (e.g. `AvoidCatchingThrowable` no longer exists in 10.x - `IllegalCatch` covers
> that already). If an upgrade fails, read the `Unable to instantiate '<X>'` line and delete that module.

## Run it fast, with no build tool

```bash
JAR=/tmp/checkstyle-10.21.4-all.jar
[ -f "$JAR" ] || curl -sSL -o "$JAR" \
  https://github.com/checkstyle/checkstyle/releases/download/checkstyle-10.21.4/checkstyle-10.21.4-all.jar
java -jar "$JAR" -c configs/java/checkstyle.xml src/main/java
```

## Maven

```xml
<plugin>
  <groupId>org.apache.maven.plugins</groupId>
  <artifactId>maven-checkstyle-plugin</artifactId>
  <version>3.6.0</version>
  <dependencies>
    <dependency>
      <groupId>com.puppycrawl.tools</groupId>
      <artifactId>checkstyle</artifactId>
      <version>10.21.4</version>
    </dependency>
  </dependencies>
  <configuration>
    <configLocation>configs/java/checkstyle.xml</configLocation>
    <consoleOutput>true</consoleOutput>
    <failsOnError>true</failsOnError>
    <violationSeverity>warning</violationSeverity>
  </configuration>
  <executions>
    <execution><id>checkstyle</id><phase>validate</phase>
      <goals><goal>check</goal></goals></execution>
  </executions>
</plugin>
```

## Gradle (Kotlin DSL)

```kotlin
plugins { checkstyle }
checkstyle {
    toolVersion = "10.21.4"
    configFile = rootProject.file("configs/java/checkstyle.xml")
    isShowViolations = true
    maxWarnings = 0        // 0 = strict; raise it while onboarding legacy code
}
tasks.withType<Checkstyle>().configureEach { reports { xml.required = true } }
```

## Deliberate exceptions

```java
// CHECKSTYLE:OFF MagicNumber - statutory tax-rate table fixed by law, see ADR-0007
private static final double[] BRACKETS = {0.05, 0.1, 0.15};
// CHECKSTYLE:ON
```

Never disable a whole file. Disable **one rule, one range, with a reason and a document link** -
that is the minimum discipline that keeps a rule meaningful. See `../../playbook/09-code-health-and-workflow.md`.

## Demo

* `demo/OrderTotalsBad.java` - deliberately wrong: 6 parameters, 5 magic numbers, an empty catch, a TODO.
  Measured: `java -jar checkstyle.jar -c checkstyle.xml demo/OrderTotalsBad.java` → **8 audit messages**
  (get the JAR: `curl -sLO https://github.com/checkstyle/checkstyle/releases/download/checkstyle-10.21.4/checkstyle-10.21.4-all.jar`
  - it is not vendored here)
  = 7 WARN (1 `ParameterNumber` line 9 + 5 `MagicNumber` lines 23, 24, 26, 30, 34 + 1 `EmptyCatchBlock`
line 35) and 1 INFO (`TodoComment` line 3). Counting only WARN gives 7; the exit code is what CI reads.
  `LineLength` and `MethodLength` stay **silent**: the demo keeps its functions under the limit - it breaks
  only the rules the config actually tightens, rather than being padded to look bad.
* `demo/OrderTotalsGood.java` - 0 violations: named constants, guard clauses, functions <= 40 lines
