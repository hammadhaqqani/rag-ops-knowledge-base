# High CPU Usage Troubleshooting Guide

## Problem Description

System or application is experiencing high CPU utilization, causing performance degradation, slow response times, or service unavailability.

## Symptoms and Indicators

- CPU utilization consistently above 80-90%
- Slow application response times
- Timeout errors
- System load average exceeding CPU core count
- CloudWatch/ monitoring alerts for high CPU
- User complaints about slow performance
- Process queue building up

## Prerequisites

- System access (SSH or console)
- Monitoring tools access (CloudWatch, Datadog, etc.)
- Process inspection tools (top, htop, ps)
- Application logs access
- Understanding of normal system baseline

## Step-by-Step Troubleshooting Procedure

### Step 1: Identify High CPU Processes

1. **Check overall CPU usage**:
   ```bash
   top
   # Press '1' to see per-CPU usage
   # Press 'P' to sort by CPU
   ```

2. **Alternative tools**:
   ```bash
   htop  # More user-friendly
   ps aux --sort=-%cpu | head -20  # Top CPU processes
   ```

3. **For containers**:
   ```bash
   docker stats
   # or for Kubernetes
   kubectl top pods -n <namespace>
   kubectl top nodes
   ```

### Step 2: Analyze Process Details

1. **Get detailed process information**:
   ```bash
   ps -p <PID> -o pid,ppid,cmd,%mem,%cpu,etime
   ```

2. **Check process threads**:
   ```bash
   top -H -p <PID>  # Show threads
   # or
   ps -T -p <PID>  # Thread information
   ```

3. **Check process file descriptors**:
   ```bash
   lsof -p <PID> | wc -l
   ```

4. **Check process memory usage**:
   ```bash
   pmap -x <PID>
   ```

### Step 3: Common Causes and Solutions

#### Cause A: Infinite Loop or Tight Loop in Code

**Symptoms**: Single process consuming 100% of a CPU core

**Solution**:
1. Identify the process and application
2. Check application logs for errors
3. Review recent code deployments
4. Use profiling tools:
   ```bash
   # For Python
   py-spy top --pid <PID>
   
   # For Java
   jstack <PID> > thread-dump.txt
   
   # For Node.js
   node --prof <script>
   ```
5. Fix the code issue and redeploy

#### Cause B: Database Query Issues

**Symptoms**: Database connection processes with high CPU, slow queries

**Solution**:
1. Check database connections:
   ```sql
   -- PostgreSQL
   SELECT pid, usename, application_name, state, query 
   FROM pg_stat_activity 
   WHERE state = 'active';
   
   -- MySQL
   SHOW PROCESSLIST;
   ```

2. Identify slow queries:
   ```sql
   -- PostgreSQL
   SELECT * FROM pg_stat_statements 
   ORDER BY total_exec_time DESC 
   LIMIT 10;
   ```

3. Optimize or kill problematic queries:
   ```sql
   -- PostgreSQL
   SELECT pg_terminate_backend(<pid>);
   
   -- MySQL
   KILL <process_id>;
   ```

4. Review query execution plans and add indexes

#### Cause C: Resource Exhaustion Leading to Thrashing

**Symptoms**: High CPU with high I/O wait, swapping

**Solution**:
1. Check memory usage:
   ```bash
   free -h
   vmstat 1 5
   ```

2. Check swap usage:
   ```bash
   swapon --show
   cat /proc/meminfo | grep Swap
   ```

3. Identify memory-hungry processes:
   ```bash
   ps aux --sort=-%mem | head -10
   ```

4. Solutions:
   - Increase system memory
   - Optimize application memory usage
   - Add more instances (horizontal scaling)
   - Tune garbage collection (for Java/Go apps)

#### Cause D: Malicious Activity or Mining

**Symptoms**: Unknown processes, high CPU on unusual ports

**Solution**:
1. Check for suspicious processes:
   ```bash
   ps aux | grep -E "(minerd|cpuminer|xmrig)"
   netstat -tulpn | grep ESTABLISHED
   ```

2. Check cron jobs:
   ```bash
   crontab -l
   cat /etc/cron.*/*
   ```

3. Check systemd services:
   ```bash
   systemctl list-units --type=service --state=running
   ```

4. If compromised:
   - Isolate the system
   - Kill malicious processes
   - Review security logs
   - Patch vulnerabilities
   - Rotate credentials

#### Cause E: Application Scaling Issues

**Symptoms**: Legitimate high load, but insufficient capacity

**Solution**:
1. Check request rates:
   ```bash
   # Web server logs
   tail -f /var/log/nginx/access.log | awk '{print $1}' | sort | uniq -c | sort -rn
   ```

2. Review auto-scaling configuration:
   ```bash
   # AWS Auto Scaling
   aws autoscaling describe-auto-scaling-groups
   ```

3. Scale horizontally:
   - Add more application instances
   - Enable auto-scaling
   - Use load balancer

4. Scale vertically (if horizontal not possible):
   - Increase instance size
   - Add CPU cores

#### Cause F: Garbage Collection Issues (Java/Go)

**Symptoms**: Periodic CPU spikes, memory pressure

**Solution**:
1. Enable GC logging:
   ```bash
   -XX:+PrintGCDetails -XX:+PrintGCTimeStamps -Xloggc:gc.log
   ```

2. Analyze GC logs
3. Tune GC parameters:
   ```bash
   -XX:+UseG1GC
   -XX:MaxGCPauseMillis=200
   -Xmx4g -Xms4g
   ```

### Step 4: Immediate Mitigation

If immediate action is needed:

1. **Kill problematic process** (if safe):
   ```bash
   kill -15 <PID>  # SIGTERM (graceful)
   # Wait a few seconds
   kill -9 <PID>   # SIGKILL (forceful)
   ```

2. **Restart service**:
   ```bash
   systemctl restart <service-name>
   # or
   docker restart <container>
   # or
   kubectl rollout restart deployment <deployment-name>
   ```

3. **Scale up temporarily**:
   ```bash
   # Add more instances
   aws autoscaling set-desired-capacity \
     --auto-scaling-group-name <asg-name> \
     --desired-capacity <new-capacity>
   ```

4. **Rate limiting** (if applicable):
   - Implement request throttling
   - Enable rate limiting at load balancer
   - Add circuit breakers

### Step 5: Monitor and Verify

1. **Continuous monitoring**:
   ```bash
   watch -n 1 'ps aux --sort=-%cpu | head -10'
   ```

2. **Check CloudWatch/metrics**:
   - CPU utilization trending down
   - Response times improving
   - Error rates decreasing

3. **Application health checks**:
   ```bash
   curl http://localhost:8080/health
   ```

4. **User experience validation**:
   - Test critical user flows
   - Verify response times
   - Check error logs

## Verification Steps

- [ ] CPU utilization is below 70% (or normal baseline)
- [ ] System load average is acceptable
- [ ] Application response times are normal
- [ ] No processes consuming excessive CPU
- [ ] Monitoring alerts have cleared
- [ ] User-facing performance is acceptable
- [ ] No error spikes in application logs

## Escalation Procedures

If high CPU persists:

1. **Level 1**: Application Team
   - Review recent code changes
   - Profile application performance
   - Optimize hot paths

2. **Level 2**: Platform/Infrastructure Team
   - Review infrastructure capacity
   - Check for infrastructure issues
   - Consider scaling options

3. **Level 3**: Architecture Review
   - Review system architecture
   - Consider architectural changes
   - Performance testing and optimization

## Prevention Measures

- Set up CPU utilization alerts (e.g., >80% for 5 minutes)
- Regular performance testing and profiling
- Implement proper monitoring and observability
- Set resource limits (containers/Kubernetes)
- Regular code reviews focusing on performance
- Database query optimization and indexing
- Implement caching strategies
- Use connection pooling
- Regular capacity planning
- Load testing before major releases
- Implement circuit breakers and rate limiting
- Regular security audits to prevent compromise

## Related Documentation

- Linux Performance Monitoring: https://www.brendangregg.com/linuxperf.html
- CloudWatch Metrics: https://docs.aws.amazon.com/AmazonCloudWatch/latest/monitoring/working_with_metrics.html
- Application Performance Monitoring best practices

## Last Updated

2026-02-09
