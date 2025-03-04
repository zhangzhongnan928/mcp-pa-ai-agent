/**
 * Tasks Module Functions
 * Provides MCP functions for managing tasks and to-dos
 */

import config from '../../config/index.js';
import logger from '../../utils/logger.js';
import { getLocalTaskProvider } from './providers/local.js';

// Get the default task provider from config
const defaultProvider = config.modules.tasks.defaultProvider;

/**
 * Get all tasks, optionally filtered
 */
const getTasks = {
  description: "Get all tasks, optionally filtered by status, priority, or date",
  parameters: {
    properties: {
      status: {
        type: "string",
        description: "Filter by status (open, in_progress, completed)"
      },
      priority: {
        type: "string",
        description: "Filter by priority (high, medium, low)"
      },
      dueDate: {
        type: "string",
        description: "Filter by due date (YYYY-MM-DD) or relative (today, tomorrow, this_week)"
      },
      provider: {
        type: "string",
        description: "Task provider to use (local, todoist)"
      }
    },
    required: []
  },
  async handler(params) {
    try {
      const provider = params.provider || defaultProvider;
      
      logger.info(`Getting tasks using ${provider} provider with filters: ${JSON.stringify(params)}`);
      
      // Get tasks based on the provider
      if (provider === 'local') {
        const taskProvider = await getLocalTaskProvider();
        return await taskProvider.getTasks({
          status: params.status,
          priority: params.priority,
          dueDate: params.dueDate
        });
      } else {
        throw new Error(`Task provider '${provider}' is not supported or enabled`);
      }
    } catch (error) {
      logger.error(`Failed to get tasks: ${error.message}`);
      throw new Error(`Failed to get tasks: ${error.message}`);
    }
  }
};

/**
 * Get a specific task by ID
 */
const getTaskById = {
  description: "Get a specific task by ID",
  parameters: {
    properties: {
      taskId: {
        type: "string",
        description: "ID of the task to retrieve"
      },
      provider: {
        type: "string",
        description: "Task provider to use (local, todoist)"
      }
    },
    required: ["taskId"]
  },
  async handler(params) {
    try {
      const provider = params.provider || defaultProvider;
      
      logger.info(`Getting task ${params.taskId} using ${provider} provider`);
      
      // Get task based on the provider
      if (provider === 'local') {
        const taskProvider = await getLocalTaskProvider();
        return await taskProvider.getTaskById(params.taskId);
      } else {
        throw new Error(`Task provider '${provider}' is not supported or enabled`);
      }
    } catch (error) {
      logger.error(`Failed to get task: ${error.message}`);
      throw new Error(`Failed to get task: ${error.message}`);
    }
  }
};

/**
 * Create a new task
 */
const createTask = {
  description: "Create a new task",
  parameters: {
    properties: {
      title: {
        type: "string",
        description: "Title of the task"
      },
      description: {
        type: "string",
        description: "Description of the task"
      },
      dueDate: {
        type: "string",
        description: "Due date (YYYY-MM-DD) or relative (today, tomorrow)"
      },
      priority: {
        type: "string",
        description: "Priority level (high, medium, low)"
      },
      tags: {
        type: "array",
        items: {
          type: "string"
        },
        description: "Tags associated with the task"
      },
      provider: {
        type: "string",
        description: "Task provider to use (local, todoist)"
      }
    },
    required: ["title"]
  },
  async handler(params) {
    try {
      const provider = params.provider || defaultProvider;
      
      logger.info(`Creating task "${params.title}" using ${provider} provider`);
      
      // Create task based on the provider
      if (provider === 'local') {
        const taskProvider = await getLocalTaskProvider();
        return await taskProvider.createTask({
          title: params.title,
          description: params.description,
          dueDate: params.dueDate,
          priority: params.priority || 'medium',
          tags: params.tags || []
        });
      } else {
        throw new Error(`Task provider '${provider}' is not supported or enabled`);
      }
    } catch (error) {
      logger.error(`Failed to create task: ${error.message}`);
      throw new Error(`Failed to create task: ${error.message}`);
    }
  }
};

/**
 * Update an existing task
 */
const updateTask = {
  description: "Update an existing task",
  parameters: {
    properties: {
      taskId: {
        type: "string",
        description: "ID of the task to update"
      },
      title: {
        type: "string",
        description: "New title for the task"
      },
      description: {
        type: "string",
        description: "New description for the task"
      },
      dueDate: {
        type: "string",
        description: "New due date (YYYY-MM-DD) or relative (today, tomorrow)"
      },
      priority: {
        type: "string",
        description: "New priority level (high, medium, low)"
      },
      status: {
        type: "string",
        description: "New status (open, in_progress, completed)"
      },
      tags: {
        type: "array",
        items: {
          type: "string"
        },
        description: "New tags associated with the task"
      },
      provider: {
        type: "string",
        description: "Task provider to use (local, todoist)"
      }
    },
    required: ["taskId"]
  },
  async handler(params) {
    try {
      const provider = params.provider || defaultProvider;
      
      logger.info(`Updating task ${params.taskId} using ${provider} provider`);
      
      // Update task based on the provider
      if (provider === 'local') {
        const taskProvider = await getLocalTaskProvider();
        return await taskProvider.updateTask({
          id: params.taskId,
          title: params.title,
          description: params.description,
          dueDate: params.dueDate,
          priority: params.priority,
          status: params.status,
          tags: params.tags
        });
      } else {
        throw new Error(`Task provider '${provider}' is not supported or enabled`);
      }
    } catch (error) {
      logger.error(`Failed to update task: ${error.message}`);
      throw new Error(`Failed to update task: ${error.message}`);
    }
  }
};

/**
 * Delete a task
 */
const deleteTask = {
  description: "Delete a task",
  parameters: {
    properties: {
      taskId: {
        type: "string",
        description: "ID of the task to delete"
      },
      provider: {
        type: "string",
        description: "Task provider to use (local, todoist)"
      }
    },
    required: ["taskId"]
  },
  async handler(params) {
    try {
      const provider = params.provider || defaultProvider;
      
      logger.info(`Deleting task ${params.taskId} using ${provider} provider`);
      
      // Delete task based on the provider
      if (provider === 'local') {
        const taskProvider = await getLocalTaskProvider();
        return await taskProvider.deleteTask(params.taskId);
      } else {
        throw new Error(`Task provider '${provider}' is not supported or enabled`);
      }
    } catch (error) {
      logger.error(`Failed to delete task: ${error.message}`);
      throw new Error(`Failed to delete task: ${error.message}`);
    }
  }
};

/**
 * Complete a task
 */
const completeTask = {
  description: "Mark a task as completed",
  parameters: {
    properties: {
      taskId: {
        type: "string",
        description: "ID of the task to complete"
      },
      provider: {
        type: "string",
        description: "Task provider to use (local, todoist)"
      }
    },
    required: ["taskId"]
  },
  async handler(params) {
    try {
      const provider = params.provider || defaultProvider;
      
      logger.info(`Completing task ${params.taskId} using ${provider} provider`);
      
      // Complete task based on the provider
      if (provider === 'local') {
        const taskProvider = await getLocalTaskProvider();
        return await taskProvider.updateTask({
          id: params.taskId,
          status: 'completed'
        });
      } else {
        throw new Error(`Task provider '${provider}' is not supported or enabled`);
      }
    } catch (error) {
      logger.error(`Failed to complete task: ${error.message}`);
      throw new Error(`Failed to complete task: ${error.message}`);
    }
  }
};

export default [
  getTasks,
  getTaskById,
  createTask,
  updateTask,
  deleteTask,
  completeTask
];
