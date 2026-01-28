# Builder: compile the Spring Boot app using Microsoft OpenJDK 21 JDK
FROM eclipse-temurin:21-jdk AS builder
WORKDIR /workspace

# Cache gradle wrapper and dependency metadata
COPY gradlew gradlew.bat settings.gradle build.gradle ./
COPY gradle ./gradle

# Copy source
COPY src ./src

# Build the executable jar (skip tests to speed up image builds)
RUN chmod +x ./gradlew && ./gradlew bootJar --no-daemon -x test

# Create a minimal JRE from the JDK using jlink
RUN if [ -x "$JAVA_HOME/bin/jlink" ]; then \
      $JAVA_HOME/bin/jlink \
        --no-header-files --no-man-pages --compress=2 --strip-debug \
        --add-modules java.base,java.logging,java.sql,java.xml,java.naming,java.desktop,java.management,java.security.jgss,java.instrument,jdk.unsupported \
        --output /jre; \
    else \
      echo "jlink not found, skipping jlink step" && mkdir -p /jre && cp -a "$JAVA_HOME"/jre /jre || true; \
    fi

# Runtime image: small base, copy custom JRE and app jar
FROM debian:bookworm-slim AS runtime
ENV LANG C.UTF-8

# Create non-root user
RUN groupadd --gid 1000 appuser || true && useradd --uid 1000 --gid 1000 --create-home appuser || true

WORKDIR /app

# Copy JRE produced by builder
COPY --from=builder /jre /opt/jre

# Copy the assembled jar
COPY --from=builder /workspace/build/libs/*.jar /app/app.jar

# Create SQLite file inside the image (do NOT copy from host)
RUN mkdir -p /app/data && touch /app/data/sns_api.db && chown -R appuser:appuser /app

# Allow passing Codespaces envs from the host at build time; populate container ENV
ARG CODESPACE_NAME=""
ARG GITHUB_CODESPACES_PORT_FORWARDING_DOMAIN=""
ENV CODESPACE_NAME=${CODESPACE_NAME}
ENV GITHUB_CODESPACES_PORT_FORWARDING_DOMAIN=${GITHUB_CODESPACES_PORT_FORWARDING_DOMAIN}

# Expose application port
EXPOSE 8080

USER appuser

# Ensure we use the bundled JRE if present, otherwise fallback to system java
ENV PATH="/opt/jre/bin:${PATH}"

ENTRYPOINT ["/opt/jre/bin/java","-jar","/app/app.jar"]
