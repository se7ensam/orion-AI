/**
 * Shared types and configuration for Orion backend services.
 * Centralized exports for better tree-shaking and type inference.
 */

// Contract types
export type { IngestionJob } from './contracts/filing.js';

// Queue configuration  
export { QUEUE_NAME, EXCHANGE_NAME, ROUTING_KEY } from './messaging/queue-config.js';
