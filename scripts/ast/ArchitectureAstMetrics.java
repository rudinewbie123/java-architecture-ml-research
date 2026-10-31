import com.github.javaparser.*;
import com.github.javaparser.ast.CompilationUnit;
import com.github.javaparser.ast.body.*;
import com.github.javaparser.ast.expr.*;
import com.github.javaparser.ast.stmt.*;
import com.github.javaparser.ast.type.ClassOrInterfaceType;

import java.io.*;
import java.nio.file.*;
import java.util.*;
import java.util.stream.*;

public class ArchitectureAstMetrics {

    private static String csv(String value) {
        if (value == null) value = "";
        return "\"" + value.replace("\"", "\"\"") + "\"";
    }

    private static int wmc(MethodDeclaration method) {
        if (!method.getBody().isPresent()) return 1;

        BlockStmt body = method.getBody().get();
        int score = 1;

        score += body.findAll(IfStmt.class).size();
        score += body.findAll(ForStmt.class).size();
        score += body.findAll(ForEachStmt.class).size();
        score += body.findAll(WhileStmt.class).size();
        score += body.findAll(DoStmt.class).size();
        score += body.findAll(CatchClause.class).size();
        score += body.findAll(ConditionalExpr.class).size();

        for (BinaryExpr expression : body.findAll(BinaryExpr.class)) {
            if (expression.getOperator() == BinaryExpr.Operator.AND ||
                expression.getOperator() == BinaryExpr.Operator.OR) {
                score++;
            }
        }

        return score;
    }

    private static Set<String> fieldsUsed(
        MethodDeclaration method,
        Set<String> declaredFields
    ) {
        Set<String> used = new HashSet<>();

        if (!method.getBody().isPresent()) return used;

        BlockStmt body = method.getBody().get();

        for (NameExpr expression : body.findAll(NameExpr.class)) {
            String name = expression.getNameAsString();
            if (declaredFields.contains(name)) used.add(name);
        }

        for (FieldAccessExpr expression : body.findAll(FieldAccessExpr.class)) {
            String name = expression.getNameAsString();
            if (declaredFields.contains(name)) used.add(name);
        }

        return used;
    }

    // Henderson-Sellers-style pair-count proxy:
    // LCOM1 = max(P - Q, 0), where P is non-sharing pairs and
    // Q is sharing pairs. Field references are name-based, not symbol-resolved.
    private static int lcom1(List<Set<String>> methodFieldSets) {
        int p = 0;
        int q = 0;

        for (int i = 0; i < methodFieldSets.size(); i++) {
            for (int j = i + 1; j < methodFieldSets.size(); j++) {
                Set<String> intersection = new HashSet<>(methodFieldSets.get(i));
                intersection.retainAll(methodFieldSets.get(j));

                if (intersection.isEmpty()) p++;
                else q++;
            }
        }

        return Math.max(0, p - q);
    }

    private static void writeType(
        PrintWriter writer,
        String candidateId,
        String commitSha,
        String architecture,
        String domain,
        String sourceFile,
        String packageName,
        TypeDeclaration<?> type,
        Set<String> projectTypeNames,
        String typeKind
    ) {
        List<MethodDeclaration> methods = type.getMembers().stream()
            .filter(member -> member instanceof MethodDeclaration)
            .map(member -> (MethodDeclaration) member)
            .collect(Collectors.toList());

        Set<String> fields = new HashSet<>();

        for (BodyDeclaration<?> member : type.getMembers()) {
            if (member instanceof FieldDeclaration) {
                for (VariableDeclarator variable :
                     ((FieldDeclaration) member).getVariables()) {
                    fields.add(variable.getNameAsString());
                }
            }
        }

        int wmc = methods.stream()
            .mapToInt(ArchitectureAstMetrics::wmc)
            .sum();

        Set<String> calledMethodNames = new HashSet<>();

        for (MethodDeclaration method : methods) {
            if (method.getBody().isPresent()) {
                for (MethodCallExpr call :
                     method.getBody().get().findAll(MethodCallExpr.class)) {
                    calledMethodNames.add(call.getNameAsString());
                }
            }
        }

        // Local-project type reference proxy; external library types are excluded.
        Set<String> localTypeReferences = new HashSet<>();

        for (ClassOrInterfaceType reference :
             type.findAll(ClassOrInterfaceType.class)) {
            String name = reference.getNameAsString();

            if (projectTypeNames.contains(name) &&
                !name.equals(type.getNameAsString())) {
                localTypeReferences.add(name);
            }
        }

        List<Set<String>> methodFieldSets = methods.stream()
            .map(method -> fieldsUsed(method, fields))
            .collect(Collectors.toList());

        int lcom = lcom1(methodFieldSets);

        int loc = type.getRange()
            .map(range -> range.end.line - range.begin.line + 1)
            .orElse(0);

        writer.println(
            csv(candidateId) + "," +
            csv(commitSha) + "," +
            csv(architecture) + "," +
            csv(domain) + "," +
            csv(sourceFile) + "," +
            csv(packageName) + "," +
            csv(type.getNameAsString()) + "," +
            csv(typeKind) + "," +
            methods.size() + "," +
            fields.size() + "," +
            wmc + "," +
            (methods.size() + calledMethodNames.size()) + "," +
            localTypeReferences.size() + "," +
            lcom + "," +
            loc
        );
    }

    public static void main(String[] args) throws Exception {
        if (args.length != 7) {
            System.err.println(
                "Usage: <repo> <candidate_id> <architecture> <domain> " +
                "<commit_sha> <reserved> <output_csv>"
            );
            System.exit(2);
        }

        Path repository = Paths.get(args[0]);
        String candidateId = args[1];
        String architecture = args[2];
        String domain = args[3];
        String commitSha = args[4];
        Path output = Paths.get(args[6]);

        Files.createDirectories(output.getParent());

        List<Path> javaFiles;

        try (Stream<Path> paths = Files.walk(repository)) {
            javaFiles = paths
                .filter(path -> path.toString().endsWith(".java"))
                .filter(path -> !path.toString().contains("/.git/"))
                .filter(path -> !path.toString().contains("/target/"))
                .filter(path -> !path.toString().contains("/build/"))
                .collect(Collectors.toList());
        }

        ParserConfiguration configuration = new ParserConfiguration()
            .setLanguageLevel(ParserConfiguration.LanguageLevel.JAVA_21);

        JavaParser parser = new JavaParser(configuration);

        List<CompilationUnit> units = new ArrayList<>();
        List<String[]> parseErrors = new ArrayList<>();

        for (Path javaFile : javaFiles) {
            ParseResult<CompilationUnit> result = parser.parse(javaFile);

            if (result.getResult().isPresent()) {
                units.add(result.getResult().get());
            } else {
                parseErrors.add(new String[] {
                    javaFile.toString(),
                    result.getProblems().toString()
                });
            }
        }

        Set<String> projectTypeNames = new HashSet<>();

        for (CompilationUnit unit : units) {
            for (ClassOrInterfaceDeclaration type :
                 unit.findAll(ClassOrInterfaceDeclaration.class)) {
                projectTypeNames.add(type.getNameAsString());
            }

            for (EnumDeclaration type : unit.findAll(EnumDeclaration.class)) {
                projectTypeNames.add(type.getNameAsString());
            }

            for (RecordDeclaration type : unit.findAll(RecordDeclaration.class)) {
                projectTypeNames.add(type.getNameAsString());
            }
        }

        try (PrintWriter writer =
             new PrintWriter(Files.newBufferedWriter(output))) {

            writer.println(
                "candidate_id,commit_sha,architecture_label,domain," +
                "source_file,package_name,type_name,type_kind," +
                "method_count,field_count,wmc_ast,rfc_source_proxy," +
                "cbo_local_type_proxy,lcom1_name_based_proxy,physical_loc"
            );

            for (CompilationUnit unit : units) {
                String packageName = unit.getPackageDeclaration()
                    .map(declaration -> declaration.getNameAsString())
                    .orElse("(default)");

                String sourceFile = unit.getStorage()
                    .map(storage -> storage.getPath().toString())
                    .orElse("");

                for (ClassOrInterfaceDeclaration type :
                     unit.findAll(ClassOrInterfaceDeclaration.class)) {
                    if (!type.isInterface()) {
                        writeType(
                            writer, candidateId, commitSha, architecture,
                            domain, sourceFile, packageName, type,
                            projectTypeNames, "class"
                        );
                    }
                }

                for (EnumDeclaration type :
                     unit.findAll(EnumDeclaration.class)) {
                    writeType(
                        writer, candidateId, commitSha, architecture,
                        domain, sourceFile, packageName, type,
                        projectTypeNames, "enum"
                    );
                }

                for (RecordDeclaration type :
                     unit.findAll(RecordDeclaration.class)) {
                    writeType(
                        writer, candidateId, commitSha, architecture,
                        domain, sourceFile, packageName, type,
                        projectTypeNames, "record"
                    );
                }
            }
        }

        Path errorFile = output.resolveSibling(
            candidateId + "_parse_errors.csv"
        );

        try (PrintWriter writer =
             new PrintWriter(Files.newBufferedWriter(errorFile))) {
            writer.println("source_file,parse_problem");

            for (String[] error : parseErrors) {
                writer.println(csv(error[0]) + "," + csv(error[1]));
            }
        }

        System.out.println(
            "java_files=" + javaFiles.size() +
            " parsed_units=" + units.size() +
            " parse_errors=" + parseErrors.size()
        );
    }
}
