// ResQNet AI - MongoDB Initialization Script
// Creates the resqnet database and required collections with validation rules

db = db.getSiblingDB('resqnet');

// Create collections
db.createCollection('users');
db.createCollection('incidents');
db.createCollection('resources');
db.createCollection('shelters');
db.createCollection('hospitals');
db.createCollection('audit_logs');
db.createCollection('command_briefs');

print('ResQNet AI database initialized successfully');
