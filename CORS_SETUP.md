# CORS Configuration for KoraQuest API

This guide explains the CORS (Cross-Origin Resource Sharing) configuration for your KoraQuest API.

## 🔧 Current CORS Setup

### ✅ What's Already Configured

1. **django-cors-headers** package is installed
2. **CORS middleware** is properly positioned in MIDDLEWARE
3. **Basic CORS settings** are configured

### 📋 CORS Settings Explained

```python
# CORS Settings
CORS_ALLOWED_ORIGINS = [
    "http://localhost:3000",      # React development server
    "http://127.0.0.1:3000",      # Alternative localhost
    "https://koraquest.bonasolutions.tech",  # Production domain
]

CORS_ALLOW_CREDENTIALS = True  # Allows cookies and authentication headers
```

## 🚀 Development vs Production

### Development Settings
```python
# For development - allows all origins (NOT for production!)
if DEBUG:
    CORS_ALLOW_ALL_ORIGINS = True
    CORS_ALLOWED_ORIGIN_REGEXES = [
        r"^http://localhost:\d+$",    # Any localhost port
        r"^http://127\.0\.0\.1:\d+$", # Any 127.0.0.1 port
    ]
```

### Production Settings
```python
# For production - specific origins only
CORS_ALLOWED_ORIGINS = [
    "https://koraquest.bonasolutions.tech",
    "https://www.koraquest.bonasolutions.tech",
    "https://app.koraquest.bonasolutions.tech",
]
```

## 🔐 Security Considerations

### ✅ Secure Configuration
- **Specific Origins**: Only allow trusted domains
- **Credentials**: Only enable when needed
- **Headers**: Only allow necessary headers
- **Methods**: Only allow required HTTP methods

### ❌ Avoid These in Production
```python
# DON'T use these in production!
CORS_ALLOW_ALL_ORIGINS = True
CORS_ALLOW_CREDENTIALS = True  # Only if you need cookies/auth
```

## 📱 Frontend Integration

### React.js Example
```javascript
// API client configuration
const API_BASE_URL = 'http://localhost:8000/auth/api/rest/';

// Fetch with credentials
fetch(`${API_BASE_URL}users/me/`, {
    method: 'GET',
    credentials: 'include',  // Include cookies
    headers: {
        'Content-Type': 'application/json',
        'X-CSRFToken': getCsrfToken(),  // For CSRF protection
    },
})
.then(response => response.json())
.then(data => console.log(data));
```

### Vue.js Example
```javascript
// Axios configuration
import axios from 'axios';

const api = axios.create({
    baseURL: 'http://localhost:8000/auth/api/rest/',
    withCredentials: true,  // Include cookies
    headers: {
        'Content-Type': 'application/json',
    },
});

// Add CSRF token to requests
api.interceptors.request.use((config) => {
    const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]')?.value;
    if (csrfToken) {
        config.headers['X-CSRFToken'] = csrfToken;
    }
    return config;
});
```

### Angular Example
```typescript
// HTTP client configuration
import { HttpClient } from '@angular/common/http';

@Injectable()
export class ApiService {
    private baseUrl = 'http://localhost:8000/auth/api/rest/';
    
    constructor(private http: HttpClient) {}
    
    getUsers() {
        return this.http.get(`${this.baseUrl}users/`, {
            withCredentials: true  // Include cookies
        });
    }
}
```

## 🧪 Testing CORS

### Test CORS with curl
```bash
# Test preflight request
curl -X OPTIONS http://localhost:8000/auth/api/rest/users/ \
  -H "Origin: http://localhost:3000" \
  -H "Access-Control-Request-Method: GET" \
  -H "Access-Control-Request-Headers: Content-Type" \
  -v

# Test actual request
curl -X GET http://localhost:8000/auth/api/rest/users/ \
  -H "Origin: http://localhost:3000" \
  -H "Content-Type: application/json" \
  -v
```

### Test CORS with JavaScript
```javascript
// Test CORS from browser console
fetch('http://localhost:8000/auth/api/rest/users/', {
    method: 'GET',
    credentials: 'include',
    headers: {
        'Content-Type': 'application/json',
    },
})
.then(response => {
    console.log('CORS headers:', response.headers);
    return response.json();
})
.then(data => console.log('Data:', data))
.catch(error => console.error('CORS Error:', error));
```

## 🐛 Common CORS Issues

### Issue 1: "Access to fetch blocked by CORS policy"
**Solution**: Add your frontend domain to `CORS_ALLOWED_ORIGINS`

### Issue 2: "Credentials flag is true but origin is not allowed"
**Solution**: Ensure your origin is in `CORS_ALLOWED_ORIGINS` and `CORS_ALLOW_CREDENTIALS = True`

### Issue 3: "Request header field is not allowed"
**Solution**: Add the header to `CORS_ALLOW_HEADERS`

### Issue 4: "Method is not allowed"
**Solution**: Add the method to `CORS_ALLOW_METHODS`

## 🔧 Advanced CORS Configuration

### Custom CORS Headers
```python
# Add custom headers
CORS_ALLOW_HEADERS = [
    'accept',
    'accept-encoding',
    'authorization',
    'content-type',
    'dnt',
    'origin',
    'user-agent',
    'x-csrftoken',
    'x-requested-with',
    'x-api-key',  # Custom API key header
    'x-client-version',  # Custom client version header
]
```

### Environment-Specific Origins
```python
import os

# Environment-specific CORS origins
if os.getenv('ENVIRONMENT') == 'production':
    CORS_ALLOWED_ORIGINS = [
        "https://koraquest.bonasolutions.tech",
        "https://www.koraquest.bonasolutions.tech",
    ]
elif os.getenv('ENVIRONMENT') == 'staging':
    CORS_ALLOWED_ORIGINS = [
        "https://staging.koraquest.bonasolutions.tech",
    ]
else:  # development
    CORS_ALLOWED_ORIGINS = [
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ]
```

### Dynamic CORS Origins
```python
# Allow origins from database
def get_cors_origins():
    from .models import AllowedOrigin
    return [origin.url for origin in AllowedOrigin.objects.filter(active=True)]

CORS_ALLOWED_ORIGINS = get_cors_origins()
```

## 📊 Monitoring CORS

### Log CORS Requests
```python
# Add to settings.py for debugging
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'cors_file': {
            'level': 'DEBUG',
            'class': 'logging.FileHandler',
            'filename': 'cors.log',
        },
    },
    'loggers': {
        'corsheaders': {
            'handlers': ['cors_file'],
            'level': 'DEBUG',
            'propagate': True,
        },
    },
}
```

## 🚀 Deployment Checklist

### Pre-deployment
- [ ] Remove `CORS_ALLOW_ALL_ORIGINS = True`
- [ ] Set specific production origins
- [ ] Test CORS with production domains
- [ ] Verify credentials setting
- [ ] Check allowed headers and methods

### Post-deployment
- [ ] Test API calls from frontend
- [ ] Verify preflight requests work
- [ ] Check browser console for CORS errors
- [ ] Monitor CORS logs

## 📚 Additional Resources

- [django-cors-headers Documentation](https://github.com/adamchainz/django-cors-headers)
- [MDN CORS Guide](https://developer.mozilla.org/en-US/docs/Web/HTTP/CORS)
- [Django REST Framework CORS](https://www.django-rest-framework.org/topics/ajax-csrf-cors/)

## 🆘 Troubleshooting

### Debug CORS Issues
1. Check browser developer tools Network tab
2. Look for preflight OPTIONS requests
3. Verify CORS headers in response
4. Check Django logs for CORS middleware messages

### Common Solutions
1. **Add origin to CORS_ALLOWED_ORIGINS**
2. **Enable CORS_ALLOW_CREDENTIALS if using cookies**
3. **Add custom headers to CORS_ALLOW_HEADERS**
4. **Check middleware order (CORS should be first)**
