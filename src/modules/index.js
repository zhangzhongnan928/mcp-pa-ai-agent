/**
 * MCP PA Agent Modules
 * This file exports all the function modules that will be exposed through the MCP server
 */

import calendarFunctions from './calendar/index.js';
import taskFunctions from './tasks/index.js';
import emailFunctions from './email/index.js';
import knowledgeFunctions from './knowledge/index.js';
import smartHomeFunctions from './smartHome/index.js';

// Combine all module functions
const allFunctions = [
  ...calendarFunctions,
  ...taskFunctions,
  ...emailFunctions,
  ...knowledgeFunctions,
  ...smartHomeFunctions
];

export default allFunctions;
