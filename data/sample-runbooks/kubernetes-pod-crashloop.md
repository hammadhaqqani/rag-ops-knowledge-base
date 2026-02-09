# Kubernetes Pod CrashLoopBackOff Troubleshooting

## Problem Description

A Kubernetes pod is stuck in CrashLoopBackOff state, indicating the container is repeatedly crashing and Kubernetes is backing off before restarting it.

## Symptoms and Indicators

- Pod status shows `CrashLoopBackOff` or `Error`
- `kubectl get pods` shows restart count > 0
- Application logs show repeated errors
- Pod events indicate container exit
- Health check failures
- Resource constraints (CPU/memory limits)

## Prerequisites

- `kubectl` configured with cluster access
- Appropriate RBAC permissions
- Access to pod logs and events
- Understanding of application architecture

## Step-by-Step Troubleshooting Procedure

### Step 1: Identify the Affected Pod

1. List pods and check status:
   ```bash
   kubectl get pods -n <namespace>
   ```

2. Identify pods in CrashLoopBackOff:
   ```bash
   kubectl get pods -n <namespace> | grep CrashLoopBackOff
   ```

3. Get detailed pod information:
   ```bash
   kubectl describe pod <pod-name> -n <namespace>
   ```

### Step 2: Examine Pod Events

1. Check recent events:
   ```bash
   kubectl get events -n <namespace> --sort-by='.lastTimestamp' | grep <pod-name>
   ```

2. Look for:
   - Container start/exit events
   - Image pull errors
   - Resource quota issues
   - Node scheduling problems

### Step 3: Review Container Logs

1. Get current container logs:
   ```bash
   kubectl logs <pod-name> -n <namespace>
   ```

2. Get logs from previous container instance:
   ```bash
   kubectl logs <pod-name> -n <namespace> --previous
   ```

3. Follow logs in real-time:
   ```bash
   kubectl logs <pod-name> -n <namespace> -f
   ```

4. Check logs from specific container (if multi-container pod):
   ```bash
   kubectl logs <pod-name> -c <container-name> -n <namespace>
   ```

### Step 4: Common Causes and Solutions

#### Cause A: Application Startup Errors

**Symptoms**: Application crashes immediately on startup, logs show configuration errors

**Solution**:
1. Review application configuration:
   ```bash
   kubectl get configmap <configmap-name> -n <namespace> -o yaml
   ```

2. Check environment variables:
   ```bash
   kubectl exec <pod-name> -n <namespace> -- env
   ```

3. Verify secrets are correctly mounted:
   ```bash
   kubectl get secret <secret-name> -n <namespace> -o yaml
   ```

4. Fix configuration and restart pod:
   ```bash
   kubectl delete pod <pod-name> -n <namespace>
   ```

#### Cause B: Resource Constraints

**Symptoms**: OOMKilled events, CPU throttling, memory limits exceeded

**Solution**:
1. Check resource requests/limits:
   ```bash
   kubectl describe pod <pod-name> -n <namespace> | grep -A 5 "Limits\|Requests"
   ```

2. Review node resources:
   ```bash
   kubectl top nodes
   kubectl top pod <pod-name> -n <namespace>
   ```

3. Adjust resource limits in deployment:
   ```bash
   kubectl edit deployment <deployment-name> -n <namespace>
   ```

4. Update resources section:
   ```yaml
   resources:
     requests:
       memory: "256Mi"
       cpu: "250m"
     limits:
       memory: "512Mi"
       cpu: "500m"
   ```

#### Cause C: Health Check Failures

**Symptoms**: Liveness/readiness probe failures, pod restarts after startup

**Solution**:
1. Check probe configuration:
   ```bash
   kubectl get deployment <deployment-name> -n <namespace> -o yaml | grep -A 10 "livenessProbe\|readinessProbe"
   ```

2. Test health endpoint manually:
   ```bash
   kubectl exec <pod-name> -n <namespace> -- curl http://localhost:8080/health
   ```

3. Adjust probe settings:
   - Increase `initialDelaySeconds`
   - Adjust `timeoutSeconds` and `periodSeconds`
   - Fix health endpoint implementation

#### Cause D: Image Pull Errors

**Symptoms**: ImagePullBackOff or ErrImagePull events

**Solution**:
1. Check image pull secrets:
   ```bash
   kubectl get secrets -n <namespace> | grep docker
   ```

2. Verify image exists and is accessible:
   ```bash
   docker pull <image-name>:<tag>
   ```

3. Update image pull secret if needed:
   ```bash
   kubectl create secret docker-registry <secret-name> \
     --docker-server=<registry> \
     --docker-username=<user> \
     --docker-password=<password> \
     -n <namespace>
   ```

#### Cause E: Dependency Issues

**Symptoms**: Connection errors to databases, services, or external APIs

**Solution**:
1. Check service connectivity:
   ```bash
   kubectl get svc -n <namespace>
   kubectl exec <pod-name> -n <namespace> -- nslookup <service-name>
   ```

2. Verify network policies:
   ```bash
   kubectl get networkpolicies -n <namespace>
   ```

3. Test connectivity from pod:
   ```bash
   kubectl exec <pod-name> -n <namespace> -- curl http://<service-name>:<port>
   ```

### Step 5: Temporary Workaround

If immediate fix is needed:

1. **Scale down and up**:
   ```bash
   kubectl scale deployment <deployment-name> --replicas=0 -n <namespace>
   kubectl scale deployment <deployment-name> --replicas=1 -n <namespace>
   ```

2. **Delete pod** (if part of ReplicaSet):
   ```bash
   kubectl delete pod <pod-name> -n <namespace>
   ```

3. **Restart deployment**:
   ```bash
   kubectl rollout restart deployment <deployment-name> -n <namespace>
   ```

### Step 6: Verify Resolution

1. Check pod status:
   ```bash
   kubectl get pods -n <namespace> -w
   ```

2. Verify pod is running:
   ```bash
   kubectl get pod <pod-name> -n <namespace> -o jsonpath='{.status.phase}'
   ```

3. Test application functionality:
   ```bash
   kubectl port-forward <pod-name> 8080:8080 -n <namespace>
   curl http://localhost:8080
   ```

4. Monitor for stability:
   ```bash
   kubectl get pods -n <namespace> --watch
   ```

## Verification Steps

- [ ] Pod status is `Running`
- [ ] Restart count is stable (not increasing)
- [ ] Container logs show no errors
- [ ] Health checks are passing
- [ ] Application endpoints respond correctly
- [ ] No resource constraint warnings
- [ ] Pod events show no errors

## Escalation Procedures

If troubleshooting doesn't resolve the issue:

1. **Level 1**: Application Developer
   - Review application code changes
   - Check recent deployments
   - Review application-specific configuration

2. **Level 2**: Platform/DevOps Team
   - Review cluster resources
   - Check node health
   - Review cluster-level policies

3. **Level 3**: Kubernetes Administrator
   - Deep dive into cluster configuration
   - Review CNI/networking issues
   - Check storage/volume issues

## Prevention Measures

- Implement proper health checks (liveness and readiness)
- Set appropriate resource requests and limits
- Use init containers for dependency checks
- Implement graceful shutdown handling
- Regular pod restart monitoring
- Set up alerts for CrashLoopBackOff
- Regular testing of pod startup procedures
- Document application startup requirements
- Use ConfigMaps and Secrets properly
- Implement proper error handling and logging

## Related Documentation

- Kubernetes Troubleshooting: https://kubernetes.io/docs/tasks/debug/
- Pod Lifecycle: https://kubernetes.io/docs/concepts/workloads/pods/pod-lifecycle/
- Debugging Pods: https://kubernetes.io/docs/tasks/debug/debug-application/debug-pods/

## Last Updated

2026-02-09
