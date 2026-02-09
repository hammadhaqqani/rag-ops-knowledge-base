# RDS Database Failover Procedure

## Problem Description

An RDS database instance has failed or become unavailable, requiring failover to a standby replica or promotion of a read replica to primary.

## Symptoms and Indicators

- Primary database instance status shows "failed" or "incompatible-parameters"
- Application connection errors to database
- CloudWatch alarms for database availability
- High CPU, memory, or I/O metrics before failure
- Database logs showing critical errors
- Multi-AZ failover has occurred automatically (check events)

## Prerequisites

- AWS CLI configured with database access permissions
- Access to RDS Console
- Database endpoint information
- Application configuration access (to update connection strings)
- Backup verification completed

## Step-by-Step Failover Procedure

### Step 1: Assess Database Status

1. Check RDS instance status:
   ```bash
   aws rds describe-db-instances --db-instance-identifier my-database
   ```

2. Review CloudWatch metrics:
   - DatabaseConnections
   - CPUUtilization
   - FreeableMemory
   - ReadLatency/WriteLatency
   - DiskQueueDepth

3. Check recent events:
   ```bash
   aws rds describe-events --source-identifier my-database --source-type db-instance
   ```

### Step 2: Determine Failover Strategy

#### Scenario A: Multi-AZ Deployment (Automatic Failover)

1. If Multi-AZ is enabled, failover may have occurred automatically
2. Verify new primary endpoint:
   ```bash
   aws rds describe-db-instances --db-instance-identifier my-database \
     --query 'DBInstances[0].Endpoint.Address'
   ```
3. Update application connection strings if endpoint changed
4. Monitor failover event completion

#### Scenario B: Manual Failover (Multi-AZ)

1. Initiate manual failover:
   ```bash
   aws rds reboot-db-instance \
     --db-instance-identifier my-database \
     --force-failover
   ```

2. Wait for failover to complete (typically 60-120 seconds)
3. Verify new primary is accessible
4. Update application endpoints

#### Scenario C: Promote Read Replica

1. Identify available read replica:
   ```bash
   aws rds describe-db-instances \
     --query 'DBInstances[?ReadReplicaSourceDBInstanceIdentifier!=null]'
   ```

2. Promote read replica to standalone:
   ```bash
   aws rds promote-read-replica \
     --db-instance-identifier my-read-replica
   ```

3. Wait for promotion to complete (5-15 minutes)
4. Update application connection strings
5. Create new read replicas from promoted instance

### Step 3: Verify Database Functionality

1. Test database connectivity:
   ```bash
   mysql -h new-endpoint.rds.amazonaws.com -u admin -p
   # or
   psql -h new-endpoint.rds.amazonaws.com -U postgres
   ```

2. Run basic queries:
   ```sql
   SELECT 1;
   SHOW DATABASES;
   SELECT COUNT(*) FROM important_table;
   ```

3. Check replication lag (if applicable):
   ```sql
   SHOW SLAVE STATUS\G
   ```

4. Verify application can connect and perform operations

### Step 4: Update Application Configuration

1. Update connection strings in:
   - Application configuration files
   - Environment variables
   - Secrets manager
   - Parameter store

2. Restart application services:
   ```bash
   # Example for ECS
   aws ecs update-service --cluster my-cluster --service my-service --force-new-deployment
   ```

3. Verify application logs show successful database connections

### Step 5: Post-Failover Actions

1. **Document the incident**:
   - Root cause analysis
   - Failover time and duration
   - Data loss assessment (if any)
   - Application impact

2. **Restore Multi-AZ or Read Replicas**:
   ```bash
   # Create new read replica
   aws rds create-db-instance-read-replica \
     --db-instance-identifier new-replica \
     --source-db-instance-identifier promoted-primary
   ```

3. **Review and update**:
   - Backup retention policies
   - Monitoring and alerting
   - Failover testing procedures
   - Disaster recovery runbooks

4. **Investigate root cause**:
   - Review database logs
   - Analyze CloudWatch metrics
   - Check for configuration issues
   - Review recent changes

## Verification Steps

- [ ] Database instance is in "available" state
- [ ] Database endpoint is accessible
- [ ] Application can connect to database
- [ ] Basic queries execute successfully
- [ ] No data corruption detected
- [ ] CloudWatch metrics show normal values
- [ ] Application logs show no database errors
- [ ] Read replicas are synchronized (if applicable)

## Rollback Procedure

If failover causes issues:

1. **For Multi-AZ failover**:
   - Failover back to original primary (if it recovered)
   - Or restore from latest backup

2. **For Read Replica promotion**:
   - Restore from backup to original primary
   - Re-create read replicas
   - Update application endpoints

3. **Restore from backup**:
   ```bash
   aws rds restore-db-instance-from-db-snapshot \
     --db-instance-identifier restored-db \
     --db-snapshot-identifier my-snapshot
   ```

## Escalation Procedures

If failover fails or data loss is suspected:

1. **Level 1**: AWS Support
   - Open support case with RDS team
   - Provide instance identifier and error messages

2. **Level 2**: Database Administrator
   - Review database configuration
   - Assess data integrity
   - Consider point-in-time recovery

3. **Level 3**: Incident Response Team
   - If multiple databases affected
   - If significant data loss occurred
   - If security breach suspected

## Prevention Measures

- Enable Multi-AZ deployment for production databases
- Regular automated backups with point-in-time recovery
- Monitor database health metrics
- Set up automated failover testing
- Use read replicas for read-heavy workloads
- Regular database maintenance windows
- Review and optimize database parameters
- Implement connection pooling
- Set up CloudWatch alarms for critical metrics

## Related Documentation

- RDS Multi-AZ: https://docs.aws.amazon.com/AmazonRDS/latest/UserGuide/Concepts.MultiAZ.html
- RDS Read Replicas: https://docs.aws.amazon.com/AmazonRDS/latest/UserGuide/USER_ReadRepl.html
- RDS Backup and Restore: https://docs.aws.amazon.com/AmazonRDS/latest/UserGuide/CHAP_CommonTasks.BackupRestore.html

## Last Updated

2026-02-09
