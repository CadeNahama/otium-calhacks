# Database Changes for State-Aware Step Execution

## Overview

This document outlines the database schema changes required to implement **Cursor-like state-aware step execution** in the Ping AI Agent. The current system generates all command steps upfront and executes them statically. The new system will generate steps dynamically based on real-time system state evaluation.

## Current Architecture Issues

### **Static Step Generation**
- All command steps generated upfront before execution
- No adaptation to system state changes during execution
- No ability to recover from unexpected failures or state changes
- Limited context awareness between steps

### **Missing State Tracking**
- No capture of system state before/after each step
- No comparison of state changes between steps
- No evaluation of step success based on actual outcomes
- No adaptive step generation based on current state

## Required Database Changes

### 1. New Table: `command_steps`

**Purpose**: Store individual command steps with state tracking and adaptive generation capabilities.

```sql
CREATE TABLE command_steps (
    id VARCHAR PRIMARY KEY,
    command_id VARCHAR NOT NULL REFERENCES commands(id) ON DELETE CASCADE,
    step_index INTEGER NOT NULL,
    step_type VARCHAR DEFAULT 'generated', -- 'generated', 'adaptive', 'corrective'
    command TEXT NOT NULL,
    explanation TEXT,
    risk_level VARCHAR DEFAULT 'medium',
    status VARCHAR DEFAULT 'pending', -- 'pending', 'approved', 'executing', 'completed', 'failed', 'skipped'
    execution_result JSONB, -- Results from step execution
    system_state_before JSONB, -- System state before step execution
    system_state_after JSONB, -- System state after step execution
    expected_outcome TEXT, -- What this step should achieve
    generated_at TIMESTAMP DEFAULT NOW(),
    executed_at TIMESTAMP,
    completed_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);
```

**Key Fields Explained**:
- `step_type`: Distinguishes between initial generated steps, adaptive steps based on state, and corrective steps
- `system_state_before/after`: Captures system state snapshots for comparison
- `expected_outcome`: What the step should achieve (for success evaluation)
- `execution_result`: Detailed results including stdout, stderr, exit codes

### 2. New Table: `system_state_snapshots`

**Purpose**: Store detailed system state snapshots for comparison and analysis.

```sql
CREATE TABLE system_state_snapshots (
    id VARCHAR PRIMARY KEY,
    command_id VARCHAR NOT NULL REFERENCES commands(id) ON DELETE CASCADE,
    step_id VARCHAR REFERENCES command_steps(id) ON DELETE CASCADE,
    snapshot_type VARCHAR NOT NULL, -- 'before_step', 'after_step', 'baseline'
    system_info JSONB NOT NULL, -- Complete system state
    services_status JSONB, -- Running/stopped services
    packages_installed JSONB, -- Installed packages
    network_connections JSONB, -- Network state
    file_system_state JSONB, -- File system changes
    process_list JSONB, -- Running processes
    resource_usage JSONB, -- CPU, memory, disk usage
    created_at TIMESTAMP DEFAULT NOW()
);
```

**Key Fields Explained**:
- `snapshot_type`: When the snapshot was taken (before/after step, baseline)
- `system_info`: Core system information (OS, version, etc.)
- `services_status`: Current state of system services
- `packages_installed`: Package manager state
- `network_connections`: Network configuration and connections

### 3. New Table: `step_evaluations`

**Purpose**: Store evaluations of step success and system state changes.

```sql
CREATE TABLE step_evaluations (
    id VARCHAR PRIMARY KEY,
    step_id VARCHAR NOT NULL REFERENCES command_steps(id) ON DELETE CASCADE,
    evaluation_type VARCHAR NOT NULL, -- 'success', 'failure', 'partial', 'unexpected'
    success_indicators JSONB, -- What indicates success
    failure_indicators JSONB, -- What indicates failure
    state_changes JSONB, -- Detected changes in system state
    recommendations JSONB, -- Suggested next actions
    confidence_score DECIMAL(3,2), -- 0.00 to 1.00 confidence in evaluation
    evaluated_at TIMESTAMP DEFAULT NOW()
);
```

**Key Fields Explained**:
- `evaluation_type`: Classification of step outcome
- `success_indicators`: Evidence that step succeeded
- `failure_indicators`: Evidence that step failed
- `state_changes`: Specific changes detected in system state
- `confidence_score`: AI confidence in the evaluation

### 4. Updated Table: `commands`

**Purpose**: Add fields to support state-aware execution and adaptive step generation.

```sql
-- Add new columns to existing commands table
ALTER TABLE commands ADD COLUMN current_step_index INTEGER DEFAULT 0;
ALTER TABLE commands ADD COLUMN requires_state_evaluation BOOLEAN DEFAULT TRUE;
ALTER TABLE commands ADD COLUMN adaptive_mode BOOLEAN DEFAULT FALSE;
ALTER TABLE commands ADD COLUMN baseline_system_state JSONB;
ALTER TABLE commands ADD COLUMN last_state_evaluation TIMESTAMP;
ALTER TABLE commands ADD COLUMN state_evaluation_count INTEGER DEFAULT 0;
ALTER TABLE commands ADD COLUMN adaptive_steps_generated INTEGER DEFAULT 0;
ALTER TABLE commands ADD COLUMN corrective_steps_generated INTEGER DEFAULT 0;
```

**New Fields Explained**:
- `current_step_index`: Tracks which step is currently being processed
- `requires_state_evaluation`: Enables state-aware mode for this command
- `adaptive_mode`: Enables adaptive step generation
- `baseline_system_state`: Initial system state when command was created
- `last_state_evaluation`: When system state was last evaluated
- `state_evaluation_count`: Number of state evaluations performed
- `adaptive_steps_generated`: Count of steps generated based on state
- `corrective_steps_generated`: Count of corrective steps generated

### 5. Updated Table: `command_approvals`

**Purpose**: Add fields to support state-aware approval workflow.

```sql
-- Add new columns to existing command_approvals table
ALTER TABLE command_approvals ADD COLUMN step_id VARCHAR REFERENCES command_steps(id) ON DELETE CASCADE;
ALTER TABLE command_approvals ADD COLUMN state_context JSONB; -- System state when approved
ALTER TABLE command_approvals ADD COLUMN approval_reasoning TEXT; -- Why this step was approved
ALTER TABLE command_approvals ADD COLUMN expected_impact JSONB; -- Expected system changes
```

**New Fields Explained**:
- `step_id`: Direct reference to the specific step being approved
- `state_context`: System state when the approval decision was made
- `approval_reasoning`: Human-readable reasoning for approval
- `expected_impact`: Expected changes this step will make

## Database Relationships

### **New Relationships**
```
commands (1) → (N) command_steps
command_steps (1) → (N) step_evaluations
command_steps (1) → (N) system_state_snapshots
command_steps (1) → (N) command_approvals
commands (1) → (N) system_state_snapshots
```

### **Updated Relationships**
```
commands (1) → (N) command_steps (replaces generated_commands JSONB)
command_steps (1) → (N) command_approvals (enhanced)
```

## Migration Strategy

### **Phase 1: Schema Creation**
1. Create new tables (`command_steps`, `system_state_snapshots`, `step_evaluations`)
2. Add new columns to existing tables
3. Create indexes for performance
4. Add foreign key constraints

### **Phase 2: Data Migration**
1. Migrate existing `generated_commands` JSONB data to `command_steps` table
2. Create baseline system state snapshots for existing commands
3. Update existing command records with new fields

### **Phase 3: Application Updates**
1. Update ORM models
2. Modify API endpoints
3. Update command generation logic
4. Implement state evaluation services

## Indexes for Performance

```sql
-- Performance indexes
CREATE INDEX idx_command_steps_command_id ON command_steps(command_id);
CREATE INDEX idx_command_steps_status ON command_steps(status);
CREATE INDEX idx_command_steps_step_index ON command_steps(command_id, step_index);
CREATE INDEX idx_system_state_snapshots_command_id ON system_state_snapshots(command_id);
CREATE INDEX idx_system_state_snapshots_step_id ON system_state_snapshots(step_id);
CREATE INDEX idx_step_evaluations_step_id ON step_evaluations(step_id);
CREATE INDEX idx_commands_adaptive_mode ON commands(adaptive_mode) WHERE adaptive_mode = TRUE;
CREATE INDEX idx_commands_state_evaluation ON commands(last_state_evaluation);
```

## Data Retention Policy

### **System State Snapshots**
- Keep snapshots for 30 days after command completion
- Archive older snapshots to cold storage
- Compress JSONB data for long-term storage

### **Step Evaluations**
- Keep evaluations for 90 days after command completion
- Use for machine learning model training
- Aggregate data for analytics

### **Command Steps**
- Keep all steps permanently (audit trail)
- Compress execution results after 1 year
- Archive to cold storage after 2 years

## Benefits of These Changes

### **1. State Awareness**
- Capture system state before/after each step
- Compare state changes to evaluate success
- Adapt future steps based on actual system state

### **2. Adaptive Execution**
- Generate steps dynamically based on current state
- Recover from failures with corrective steps
- Handle unexpected system conditions

### **3. Better User Experience**
- Show real-time system state changes
- Provide context for approval decisions
- Enable informed decision making

### **4. Improved Reliability**
- Validate step success based on actual outcomes
- Detect and handle edge cases
- Reduce failed command executions

### **5. Audit and Compliance**
- Complete audit trail of system changes
- Detailed step-by-step execution history
- Compliance with enterprise security requirements

## Implementation Considerations

### **Performance Impact**
- JSONB fields provide good performance for state data
- Proper indexing prevents query performance issues
- Consider partitioning for large datasets

### **Storage Requirements**
- System state snapshots will increase storage usage
- Implement data retention policies
- Consider compression for historical data

### **Backward Compatibility**
- Existing commands continue to work
- Gradual migration to new schema
- Feature flags for enabling state-aware mode

## Next Steps

1. **Review and approve** this database design
2. **Create migration scripts** for schema changes
3. **Update ORM models** to reflect new schema
4. **Implement state evaluation services**
5. **Update API endpoints** for new workflow
6. **Test with sample data** before production deployment

---

*This document serves as the foundation for implementing state-aware step execution in the Ping AI Agent, bringing it closer to the intelligent, adaptive behavior of Cursor's step-by-step execution system.*
