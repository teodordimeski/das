package mk.ukim.finki.das.cryptoinfo.config;

import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.web.cors.CorsConfiguration;
import org.springframework.web.cors.UrlBasedCorsConfigurationSource;
import org.springframework.web.filter.CorsFilter;

@Configuration
public class CorsConfig {

    @Bean
    public CorsFilter corsFilter() {
        UrlBasedCorsConfigurationSource source = new UrlBasedCorsConfigurationSource();
        CorsConfiguration config = new CorsConfiguration();
        
        // Allow requests from all origins (all users)
        config.addAllowedOriginPattern("*");
        
        // Allow only GET requests
        config.addAllowedMethod("GET");
        config.addAllowedMethod("OPTIONS"); // Required for CORS preflight
        
        // Allow common headers
        config.addAllowedHeader("*");
        
        // Apply CORS configuration to all paths
        source.registerCorsConfiguration("/**", config);
        
        return new CorsFilter(source);
    }
}

