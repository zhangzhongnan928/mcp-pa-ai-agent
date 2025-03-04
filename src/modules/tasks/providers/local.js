/**
 * Local Task Provider
 * Manages tasks using a local JSON file storage
 */

import fs from 'fs/promises';
import path from 'path';
import { v4 as uuidv4 } from 'uuid';
import logger from '../../../utils/logger.js';
import config from '../../../config/index.js';

let localTaskProvider = null;

/**
 * Local Task Provider Class
 */
class LocalTaskProvider {
  constructor(filePath) {
    this.filePath = filePath;
    this.tasks = [];
    this.initialized = false;
  }

  /**
   * Initialize the provider and load data
   */
  async initialize() {
    if (this.initialized) {
      return;
    }

    try {
      // Ensure directory exists
      const directory = path.dirname(this.filePath);
      await fs.mkdir(directory, { recursive: true });

      // Try to load tasks from file
      try {
        const fileContent = await fs.readFile(this.filePath, 'utf8');
        this.tasks = JSON.parse(fileContent);
        logger.info(`Loaded ${this.tasks.length} tasks from ${this.filePath}`);
      } catch (error) {
        // File might not exist yet, that's ok
        if (error.code !== 'ENOENT') {
          logger.warn(`Error reading task file: ${error.message}`);
        }
        this.tasks = [];
        // Create the file with empty array
        await this.saveToFile();
        logger.info(`Created new task file at ${this.filePath}`);
      }

      this.initialized = true;
    } catch (error) {
      logger.error(`Failed to initialize local task provider: ${error.message}`);
      throw new Error(`Failed to initialize local task provider: ${error.message}`);
    }
  }

  /**
   * Save tasks to file
   */
  async saveToFile() {
    try {
      await fs.writeFile(this.filePath, JSON.stringify(this.tasks, null, 2));
      logger.info(`Saved ${this.tasks.length} tasks to ${this.filePath}`);
    } catch (error) {
      logger.error(`Failed to save tasks to file: ${error.message}`);
      throw new Error(`Failed to save tasks: ${error.message}`);
    }
  }

  /**
   * Get all tasks with optional filtering
   */
  async getTasks(filters = {}) {
    await this.initialize();

    try {
      logger.info(`Getting tasks with filters: ${JSON.stringify(filters)}`);
      
      // Start with all tasks
      let filteredTasks = [...this.tasks];
      
      // Apply status filter
      if (filters.status) {
        filteredTasks = filteredTasks.filter(task => task.status === filters.status);
      }
      
      // Apply priority filter
      if (filters.priority) {
        filteredTasks = filteredTasks.filter(task => task.priority === filters.priority);
      }
      
      // Apply due date filter
      if (filters.dueDate) {
        // Handle relative dates
        let targetDate;
        
        if (filters.dueDate === 'today') {
          targetDate = new Date().toISOString().split('T')[0];
        } else if (filters.dueDate === 'tomorrow') {
          const tomorrow = new Date();
          tomorrow.setDate(tomorrow.getDate() + 1);
          targetDate = tomorrow.toISOString().split('T')[0];
        } else if (filters.dueDate === 'this_week') {
          // Filter for the next 7 days
          const today = new Date();
          const nextWeek = new Date();
          nextWeek.setDate(today.getDate() + 7);
          
          filteredTasks = filteredTasks.filter(task => {
            if (!task.dueDate) return false;
            
            const taskDate = new Date(task.dueDate);
            return taskDate >= today && taskDate <= nextWeek;
          });
          
          // Return early since we've already applied this filter
          return {
            success: true,
            tasks: filteredTasks
          };
        } else {
          // Assume it's a specific date
          targetDate = filters.dueDate;
        }
        
        // Filter by exact date
        filteredTasks = filteredTasks.filter(task => task.dueDate === targetDate);
      }
      
      return {
        success: true,
        tasks: filteredTasks
      };
    } catch (error) {
      logger.error(`Failed to get tasks: ${error.message}`);
      throw new Error(`Failed to get tasks: ${error.message}`);
    }
  }

  /**
   * Get a task by ID
   */
  async getTaskById(taskId) {
    await this.initialize();

    try {
      logger.info(`Getting task with ID: ${taskId}`);
      
      const task = this.tasks.find(t => t.id === taskId);
      
      if (!task) {
        throw new Error(`Task with ID ${taskId} not found`);
      }
      
      return {
        success: true,
        task
      };
    } catch (error) {
      logger.error(`Failed to get task: ${error.message}`);
      throw new Error(`Failed to get task: ${error.message}`);
    }
  }

  /**
   * Create a new task
   */
  async createTask(taskData) {
    await this.initialize();

    try {
      logger.info(`Creating new task: ${taskData.title}`);
      
      // Format due date if it's relative
      let dueDate = taskData.dueDate;
      
      if (dueDate) {
        if (dueDate === 'today') {
          dueDate = new Date().toISOString().split('T')[0];
        } else if (dueDate === 'tomorrow') {
          const tomorrow = new Date();
          tomorrow.setDate(tomorrow.getDate() + 1);
          dueDate = tomorrow.toISOString().split('T')[0];
        }
      }
      
      // Create new task
      const newTask = {
        id: uuidv4(),
        title: taskData.title,
        description: taskData.description || '',
        status: 'open',
        priority: taskData.priority || 'medium',
        dueDate: dueDate,
        tags: taskData.tags || [],
        createdAt: new Date().toISOString(),
        updatedAt: new Date().toISOString()
      };
      
      // Add to tasks
      this.tasks.push(newTask);
      
      // Save to file
      await this.saveToFile();
      
      return {
        success: true,
        task: newTask
      };
    } catch (error) {
      logger.error(`Failed to create task: ${error.message}`);
      throw new Error(`Failed to create task: ${error.message}`);
    }
  }

  /**
   * Update an existing task
   */
  async updateTask(taskData) {
    await this.initialize();

    try {
      logger.info(`Updating task with ID: ${taskData.id}`);
      
      // Find task
      const taskIndex = this.tasks.findIndex(t => t.id === taskData.id);
      
      if (taskIndex === -1) {
        throw new Error(`Task with ID ${taskData.id} not found`);
      }
      
      // Get the existing task
      const existingTask = this.tasks[taskIndex];
      
      // Format due date if it's relative
      let dueDate = taskData.dueDate;
      
      if (dueDate) {
        if (dueDate === 'today') {
          dueDate = new Date().toISOString().split('T')[0];
        } else if (dueDate === 'tomorrow') {
          const tomorrow = new Date();
          tomorrow.setDate(tomorrow.getDate() + 1);
          dueDate = tomorrow.toISOString().split('T')[0];
        }
      }
      
      // Update task with new values, only if provided
      const updatedTask = {
        ...existingTask,
        title: taskData.title !== undefined ? taskData.title : existingTask.title,
        description: taskData.description !== undefined ? taskData.description : existingTask.description,
        status: taskData.status !== undefined ? taskData.status : existingTask.status,
        priority: taskData.priority !== undefined ? taskData.priority : existingTask.priority,
        dueDate: dueDate !== undefined ? dueDate : existingTask.dueDate,
        tags: taskData.tags !== undefined ? taskData.tags : existingTask.tags,
        updatedAt: new Date().toISOString()
      };
      
      // Update in array
      this.tasks[taskIndex] = updatedTask;
      
      // Save to file
      await this.saveToFile();
      
      return {
        success: true,
        task: updatedTask
      };
    } catch (error) {
      logger.error(`Failed to update task: ${error.message}`);
      throw new Error(`Failed to update task: ${error.message}`);
    }
  }

  /**
   * Delete a task
   */
  async deleteTask(taskId) {
    await this.initialize();

    try {
      logger.info(`Deleting task with ID: ${taskId}`);
      
      // Find task
      const taskIndex = this.tasks.findIndex(t => t.id === taskId);
      
      if (taskIndex === -1) {
        throw new Error(`Task with ID ${taskId} not found`);
      }
      
      // Remove from array
      this.tasks.splice(taskIndex, 1);
      
      // Save to file
      await this.saveToFile();
      
      return {
        success: true,
        message: `Task with ID ${taskId} deleted successfully`
      };
    } catch (error) {
      logger.error(`Failed to delete task: ${error.message}`);
      throw new Error(`Failed to delete task: ${error.message}`);
    }
  }
}

/**
 * Get the local task provider instance
 * @returns {Promise<LocalTaskProvider>} Local task provider instance
 */
export async function getLocalTaskProvider() {
  if (localTaskProvider) {
    return localTaskProvider;
  }

  try {
    logger.info('Initializing local task provider');

    // Check if local tasks are enabled in config
    if (!config.modules.tasks.providers.local.enabled) {
      throw new Error('Local task provider is disabled in configuration');
    }

    // Get file path from config
    const filePath = path.resolve(process.cwd(), config.modules.tasks.providers.local.storageFile);

    // Create provider
    localTaskProvider = new LocalTaskProvider(filePath);
    await localTaskProvider.initialize();

    logger.info('Local task provider initialized successfully');
    return localTaskProvider;
  } catch (error) {
    logger.error(`Failed to get local task provider: ${error.message}`);
    throw new Error(`Failed to get local task provider: ${error.message}`);
  }
}
