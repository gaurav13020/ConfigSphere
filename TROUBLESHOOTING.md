# ConfigSphere - Troubleshooting Guide

## Frontend Issues

### Issue: Frontend shows "Could not connect to API"

**Solution 1: Check if backend is running**
```bash
# Try to access the API directly
curl http://localhost:8000/api/v1/schemas/

# If no response, the backend is not running
# Start it with: docker compose up web
```

**Solution 2: Verify CORS is configured**
```bash
# Check if CORS headers are present
curl -i -H "Origin: http://localhost:3000" http://localhost:8000/api/v1/schemas/

# Look for: "Access-Control-Allow-Origin: http://localhost:3000"
```

**Solution 3: Check API URL in frontend**
```bash
# Make sure .env file has correct URL
cat frontend/.env
# Should show: VITE_API_URL=http://localhost:8000/api/v1
```

### Issue: Frontend loads but no data appears

1. **Check browser console** (F12 → Console tab):
   - Look for error messages
   - Check Network tab for failed requests

2. **Reset application state**:
   - Clear browser localStorage: `localStorage.clear()`
   - Hard refresh: Ctrl+Shift+R (or Cmd+Shift+R on Mac)

3. **Check API responses**:
   ```bash
   curl http://localhost:8000/api/v1/config-items/
   # Should return a JSON array, even if empty: []
   ```

### Issue: Buttons are not clickable or UI is frozen

**Solution:**
```bash
# Restart frontend service
docker compose restart frontend

# Or manually:
cd frontend
npm run dev
```

---

## Backend Issues

### Issue: Database connection error

**Symptom**: Error message like "could not connect to server"

**Solution 1: Verify PostgreSQL is running**
```bash
# Check if database service is running
docker compose ps db

# If not running, start it
docker compose up db
```

**Solution 2: Check database credentials**
```bash
# Verify environment variables
echo $DB_HOST $DB_PORT $DB_USER $DB_PASSWORD

# Try connecting directly
psql -U postgres -h localhost -d configsphere
```

**Solution 3: Reset database**
```bash
# WARNING: This deletes all data!
docker compose down -v
docker compose up db
docker compose run web python manage.py migrate
```

### Issue: "No such table" error

**Cause**: Database migrations haven't run

**Solution:**
```bash
# Run migrations
docker compose exec web python manage.py migrate

# Verify tables exist
docker compose exec web python manage.py shell
>>> from apps.schemas.models import Schema
>>> Schema.objects.all()
```

### Issue: 500 Internal Server Error

**Solution 1: Check backend logs**
```bash
docker compose logs -f web

# Look for stack traces and error messages
```

**Solution 2: Check your request**
```bash
# Make sure POST request has correct JSON
curl -X POST http://localhost:8000/api/v1/schemas/ \
  -H "Content-Type: application/json" \
  -d '{"name":"test","schema_json":{}}'

# Look for validation errors in response
```

**Solution 3: Verify schema is valid**
```bash
# Schema JSON must be valid JSON Schema
# Use a JSON validator: https://jsonschema.net/

# Example valid schema:
{
  "type": "object",
  "properties": {
    "timeout": {"type": "integer"}
  }
}
```

### Issue: API responses are slow

**Solution 1: Check database query performance**
```bash
# Enable query logging in Django settings
# Set DEBUG = True temporarily to see SQL queries
```

**Solution 2: Verify no migrations are pending**
```bash
docker compose exec web python manage.py showmigrations
# All should show [X] (completed)
```

**Solution 3: Restart services**
```bash
docker compose restart web
```

---

## Docker Issues

### Issue: "Port already in use"

**Symptoms**: Error like "bind: address already in use" or "Address already in use"

**Solution 1: Find and stop the conflicting process**

**Linux/Mac:**
```bash
# Find process using port 3000
lsof -i :3000

# Find process using port 8000
lsof -i :8000

# Kill the process
kill -9 <PID>
```

**Windows:**
```bash
# Find process using port 3000
netstat -ano | findstr :3000

# Kill the process
taskkill /PID <PID> /F

# Or use Docker to stop containers
docker compose down
```

**Solution 2: Use different ports**
```yaml
# Edit docker-compose.yml
services:
  web:
    ports:
      - "8001:8000"  # Changed from 8000:8000
  frontend:
    ports:
      - "3001:3000"  # Changed from 3000:3000
```

### Issue: "Cannot connect to Docker daemon"

**Solution 1: Start Docker Desktop**
- On Windows/Mac: Open Docker Desktop application
- On Linux: `systemctl start docker`

**Solution 2: Verify Docker is accessible**
```bash
docker ps

# If error, try with sudo
sudo docker ps
```

### Issue: Out of disk space

**Symptom**: Docker build fails with disk space error

**Solution:**
```bash
# Clean up Docker
docker compose down -v
docker system prune -a

# Recreate services
docker compose up --build
```

---

## Configuration Issues

### Issue: "Invalid SCHEMA_JSON" error

**Cause**: Schema JSON is not valid JSON Schema format

**Example of INVALID schema:**
```json
{
  "name": "timeout",
  "type": "integer"
}
```

**Example of VALID schema:**
```json
{
  "type": "object",
  "properties": {
    "timeout": {"type": "integer"}
  },
  "required": ["timeout"]
}
```

**Solution:**
- Use online JSON Schema validator: https://jsonschema.net
- Check schema documentation: https://json-schema.org/

### Issue: Scope hierarchy not working

**Cause**: Scope names don't match between layers

**Example WRONG:**
```bash
# Item 1: global=default
# Item 2: global=dev (different global name!)
# These won't merge - they're different globals
```

**Example RIGHT:**
```bash
# Item 1: global=default, service=payment-svc
# Item 2: global=default, region=us-west  
# Item 3: global=default
# These will merge correctly
```

**Solution:**
- Ensure all items use same global_name
- Follow consistent naming conventions

---

## API Issues

### Issue: POST request returns "This field is required"

**Cause**: Missing required fields in request body

**Solution: Check required fields**
```bash
# For creating Config Item, required fields:
{
  "key": "required",
  "scope_level": "required",  # must be: global|region|group|service
  "description": "optional"
}

# If scope_level is region, also need:
{
  "region_name": "required"
}
```

### Issue: "Invalid scope_level"

**Cause**: scope_level must be one of: global, region, group, service

**Solution:**
```bash
# CORRECT
"scope_level": "global"
"scope_level": "region"  
"scope_level": "group"
"scope_level": "service"

# WRONG
"scope_level": "Global"  # Capital G
"scope_level": "SERVICE"  # All caps
"scope_level": "service-level"  # With hyphen
```

### Issue: Version won't activate

**Cause**: Version is not in VALIDATED status

**Solution:**
```bash
# Check version status
curl http://localhost:8000/api/v1/config-versions/1/

# Response should show:
{
  "status": "validated",  # Must be validated, not draft
  ...
}

# If not validated, update schema or remove validation
```

---

## Performance Issues

### Issue: API responses are very slow

**Check 1: Database size**
```bash
docker compose exec db psql -U postgres -d configsphere -c "SELECT * FROM information_schema.tables"
docker compose exec db psql -U postgres -d configsphere -c "SELECT datname, pg_size_pretty(pg_database_size(datname)) FROM pg_database WHERE datname='configsphere'"
```

**Check 2: Number of audit events**
```bash
docker compose exec web python manage.py shell
>>> from apps.audits.models import AuditEvent
>>> AuditEvent.objects.count()
# If huge number, consider archiving old events
```

**Solution: Add pagination**
```bash
# API supports limit and offset
curl "http://localhost:8000/api/v1/audit-events/?limit=50&offset=0"
```

---

## Getting Help

### Step 1: Gather Information

```bash
# Save system information
docker compose ps > status.txt
docker compose logs > logs.txt
echo $DJANGO_SETTINGS_MODULE >> logs.txt
```

### Step 2: Check Logs

```bash
# All logs
docker compose logs

# Backend logs only
docker compose logs web

# Last 50 lines
docker compose logs --tail=50
```

### Step 3: Test API Directly

```bash
# Test without frontend
curl -i -H "Content-Type: application/json" \
  http://localhost:8000/api/v1/config-items/
```

### Step 4: Restart Everything

```bash
# Nuclear option - start fresh
docker compose down -v
docker compose up --build
```

---

## Useful Debug Commands

```bash
# Check if services are running
docker compose ps

# View logs in real-time
docker compose logs -f

# Execute command in container
docker compose exec web python manage.py shell

# View database
docker compose exec db psql -U postgres -d configsphere

# Check environment variables
docker compose exec web env

# Restart a service
docker compose restart web

# Stop all services
docker compose stop

# Remove all services and volumes
docker compose down -v

# View resource usage
docker stats
```

---

## Performance Tips

### Backend
- Use `docker compose logs` to find slow queries
- Enable Django Debug Toolbar for local development
- Consider adding caching for frequently accessed configs

### Frontend
- Use browser DevTools Network tab to identify slow requests
- Check for API calls being made multiple times
- Clear browser cache if seeing old data

### Database
- Run `ANALYZE` to update query planner statistics
- Check for missing indexes
- Monitor disk space

---

## Still Having Issues?

1. **Check all documentation**:
   - [DEPLOYMENT_GUIDE.md](./DEPLOYMENT_GUIDE.md)
   - [API_GUIDE.md](./API_GUIDE.md)
   - [backend/README.md](./backend/README.md)
   - [frontend/README.md](./frontend/README.md)

2. **Verify prerequisites**:
   - Docker Desktop running
   - Ports 3000, 8000, 5432 are free
   - Environment variables configured

3. **Try clean restart**:
   ```bash
   docker compose down -v
   docker compose up --build
   ```

4. **Check version compatibility**:
   - Python 3.10+
   - Node.js 16+
   - Docker with compose support

---

**Last Updated**: March 2026  
**For Issues**: Check GitHub Issues or contact support
