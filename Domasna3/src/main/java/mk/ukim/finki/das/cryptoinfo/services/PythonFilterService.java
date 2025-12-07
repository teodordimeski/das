package mk.ukim.finki.das.cryptoinfo.services;

import jakarta.annotation.PostConstruct;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.scheduling.annotation.Scheduled;
import org.springframework.stereotype.Service;

import java.io.BufferedReader;
import java.io.File;
import java.io.InputStreamReader;

@Service
public class PythonFilterService {

    private static final Logger logger = LoggerFactory.getLogger(PythonFilterService.class);
    private static final String PYTHON_FILTERS_DIR = "python_filters";
    private boolean startupFiltersExecuted = false;

    @PostConstruct
    public void executeStartupFilters() {
        if (startupFiltersExecuted) {
            return;
        }
        
        logger.info("🚀 Starting Python filters on application startup...");
        
        // Execute Filter1 first
        if (executePythonScript("Filter1.py")) {
            logger.info("✅ Filter1 completed successfully");
            
            // Execute Filter2 after Filter1
            if (executePythonScript("Filter2.py")) {
                logger.info("✅ Filter2 completed successfully");
                
                // Execute Filter3 after Filter2
                if (executePythonScript("Filter3.py")) {
                    logger.info("✅ Filter3 completed successfully");
                    logger.info("✅ All startup filters completed successfully");
                } else {
                    logger.error("❌ Filter3 failed during startup");
                }
            } else {
                logger.error("❌ Filter2 failed during startup");
            }
        } else {
            logger.error("❌ Filter1 failed during startup");
        }
        
        startupFiltersExecuted = true;
    }

    @Scheduled(cron = "0 0 1 * * ?") // Run daily at 1:00 AM (after midnight)
    public void executeDailyFilters() {
        logger.info("🔄 Starting daily Python filters execution...");
        
        // Execute Filter2 first
        if (executePythonScript("Filter2.py")) {
            logger.info("✅ Filter2 completed successfully");
            
            // Execute Filter3 after Filter2
            if (executePythonScript("Filter3.py")) {
                logger.info("✅ Filter3 completed successfully");
                logger.info("✅ Daily filters completed successfully");
            } else {
                logger.error("❌ Filter3 failed during daily execution");
            }
        } else {
            logger.error("❌ Filter2 failed during daily execution");
        }
    }

    private boolean executePythonScript(String scriptName) {
        try {
            File filtersDir = new File(PYTHON_FILTERS_DIR);
            if (!filtersDir.exists()) {
                logger.error("❌ Python filters directory not found: {}", PYTHON_FILTERS_DIR);
                return false;
            }

            File scriptFile = new File(filtersDir, scriptName);
            if (!scriptFile.exists()) {
                logger.error("❌ Python script not found: {}", scriptFile.getAbsolutePath());
                return false;
            }

            // Make script executable
            scriptFile.setExecutable(true);

            // Build command
            String[] command = {"python3", scriptFile.getAbsolutePath()};
            
            logger.info("📝 Executing: {}", scriptName);
            
            ProcessBuilder processBuilder = new ProcessBuilder(command);
            processBuilder.directory(new File(System.getProperty("user.dir")));
            processBuilder.redirectErrorStream(true);
            
            Process process = processBuilder.start();
            
            // Read output
            BufferedReader reader = new BufferedReader(
                new InputStreamReader(process.getInputStream())
            );
            
            String line;
            while ((line = reader.readLine()) != null) {
                logger.info("[{}] {}", scriptName, line);
            }
            
            int exitCode = process.waitFor();
            
            if (exitCode == 0) {
                logger.info("✅ {} completed with exit code: {}", scriptName, exitCode);
                return true;
            } else {
                logger.error("❌ {} failed with exit code: {}", scriptName, exitCode);
                return false;
            }
            
        } catch (Exception e) {
            logger.error("❌ Error executing {}: {}", scriptName, e.getMessage(), e);
            return false;
        }
    }
}

