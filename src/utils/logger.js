import winston from 'winston';
import path from 'path';

/**
 * Initialize the application logger
 * @returns {winston.Logger} Configured logger instance
 */
export function initializeLogger() {
  // Define log format
  const logFormat = winston.format.combine(
    winston.format.timestamp(),
    winston.format.errors({ stack: true }),
    winston.format.printf(({ level, message, timestamp, stack }) => {
      return `${timestamp} [${level.toUpperCase()}]: ${message}${stack ? '\\n' + stack : ''}`;
    })
  );

  // Create logs directory if it doesn't exist
  const logDir = path.join(process.cwd(), 'logs');
  
  // Create and configure logger
  const logger = winston.createLogger({
    level: process.env.LOG_LEVEL || 'info',
    format: logFormat,
    transports: [
      // Console output for all logs
      new winston.transports.Console({
        format: winston.format.combine(
          winston.format.colorize(),
          logFormat
        )
      }),
      
      // File output for error logs
      new winston.transports.File({ 
        filename: path.join(logDir, 'error.log'),
        level: 'error' 
      }),
      
      // File output for all logs
      new winston.transports.File({ 
        filename: path.join(logDir, 'combined.log') 
      })
    ],
    // Handle uncaught exceptions
    exceptionHandlers: [
      new winston.transports.File({ 
        filename: path.join(logDir, 'exceptions.log') 
      })
    ]
  });

  // Add handling for unhandled promise rejections
  process.on('unhandledRejection', (reason, promise) => {
    logger.error(`Unhandled Promise Rejection: ${reason}`);
  });

  return logger;
}

// Export a default logger instance for convenience
export default initializeLogger();
