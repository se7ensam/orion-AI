"use strict";
var __importDefault = (this && this.__importDefault) || function (mod) {
    return (mod && mod.__esModule) ? mod : { "default": mod };
};
Object.defineProperty(exports, "__esModule", { value: true });
exports.ENV = void 0;
const dotenv_1 = __importDefault(require("dotenv"));
dotenv_1.default.config();
exports.ENV = {
    RABBITMQ_URL: process.env.RABBITMQ_URL || 'amqp://localhost',
    DATABASE_URL: process.env.DATABASE_URL || 'postgres://localhost/orion',
    SEC_API_BASE: process.env.SEC_API_BASE || 'https://www.sec.gov/Archives',
    USER_AGENT: process.env.USER_AGENT || 'OrionData/1.0 (contact@example.com)'
};
//# sourceMappingURL=env.js.map