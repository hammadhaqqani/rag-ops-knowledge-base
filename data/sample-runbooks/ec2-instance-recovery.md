# EC2 Instance Recovery Procedure

## Problem Description

An EC2 instance has become unresponsive or failed, requiring recovery procedures to restore service availability.

## Symptoms and Indicators

- Instance status checks failing (system status check and/or instance status check)
- Application not responding to requests
- SSH connection timeouts
- CloudWatch alarms triggering for instance health
- High CPU or memory utilization before failure
- Application logs showing errors or crashes

## Prerequisites

- AWS CLI configured with appropriate permissions
- Access to AWS Console or CLI
- Instance ID or tag information to identify the affected instance
- Backup or AMI available (if data recovery is needed)

## Step-by-Step Recovery Procedure

### Step 1: Identify the Affected Instance

1. Log into AWS Console or use AWS CLI
2. Navigate to EC2 Dashboard
3. Locate the instance using:
   - Instance ID (if known)
   - Instance name tag
   - Private IP address
   - Associated resources (ELB target, Auto Scaling Group)

### Step 2: Assess Instance Status

1. Check instance state:
   ```bash
   aws ec2 describe-instance-status --instance-ids i-1234567890abcdef0
   ```

2. Review CloudWatch metrics:
   - CPU utilization
   - Network packets
   - Status check failures
   - Memory utilization (if CloudWatch agent is installed)

3. Check recent events in the instance details panel

### Step 3: Attempt Instance Recovery

#### Option A: Reboot Instance (if instance is running but unresponsive)

1. Select the instance in EC2 Console
2. Click "Instance State" → "Reboot"
3. Wait 2-5 minutes for reboot to complete
4. Verify status checks pass

#### Option B: Stop and Start Instance (if reboot fails)

1. Select the instance
2. Click "Instance State" → "Stop Instance"
3. Wait for instance to fully stop (check instance state)
4. Click "Instance State" → "Start Instance"
5. Wait for instance to reach "running" state
6. Verify status checks pass

#### Option C: Replace Instance (if stop/start fails)

1. Create a new instance from the same AMI:
   ```bash
   aws ec2 run-instances \
     --image-id ami-12345678 \
     --instance-type t3.medium \
     --subnet-id subnet-12345678 \
     --security-group-ids sg-12345678 \
     --key-name my-key-pair
   ```

2. Attach the same EBS volumes (if data needs to be preserved)
3. Update DNS records or load balancer targets
4. Verify application functionality

### Step 4: Verify Recovery

1. Check instance status checks:
   ```bash
   aws ec2 describe-instance-status --instance-ids i-1234567890abcdef0
   ```

2. Test application endpoints:
   ```bash
   curl https://your-application-endpoint.com/health
   ```

3. Verify application logs:
   ```bash
   ssh user@instance-ip
   tail -f /var/log/application.log
   ```

4. Check CloudWatch alarms return to normal state

### Step 5: Post-Recovery Actions

1. Document the incident:
   - Root cause (if identified)
   - Recovery time
   - Actions taken
   - Prevention measures

2. Review and update:
   - Auto Scaling Group configuration
   - Health check settings
   - Monitoring and alerting rules

3. If instance was replaced:
   - Terminate old instance (after verification)
   - Update infrastructure documentation
   - Review backup/AMI creation frequency

## Verification Steps

- [ ] Instance status checks are passing
- [ ] Application is responding to requests
- [ ] CloudWatch metrics show normal values
- [ ] No error logs in application logs
- [ ] DNS/load balancer routing is correct
- [ ] All dependent services are functioning

## Escalation Procedures

If recovery attempts fail:

1. **Level 1 Escalation**: Contact AWS Support
   - Provide instance ID and error messages
   - Request instance recovery assistance

2. **Level 2 Escalation**: Engage DevOps team lead
   - Review instance configuration
   - Consider alternative recovery strategies

3. **Level 3 Escalation**: Incident response team
   - If multiple instances affected
   - If data loss is suspected
   - If security breach is possible

## Prevention Measures

- Enable detailed CloudWatch monitoring
- Set up automated status check alarms
- Configure Auto Scaling for high availability
- Regular AMI creation for critical instances
- Implement health checks at application level
- Use multiple Availability Zones
- Regular backup of critical data

## Related Documentation

- AWS EC2 Instance Recovery: https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/ec2-instance-recover.html
- CloudWatch Alarms: https://docs.aws.amazon.com/AmazonCloudWatch/latest/monitoring/AlarmThatSendsEmail.html

## Last Updated

2026-02-09
