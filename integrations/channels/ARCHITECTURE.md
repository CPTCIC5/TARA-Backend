# Architecture Documentation

## System Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                         FastAPI Application                      │
└─────────────────────────────────────────────────────────────────┘
                              │
                              │ HTTP Request (user_id from JWT/session)
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                      Integration Router                          │
│  (example_router.py or your custom routers)                     │
└─────────────────────────────────────────────────────────────────┘
                              │
                              │ get_service(user_id, db)
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                    Integration Modules                           │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐          │
│  │  Gmail   │ │ Calendar │ │  Drive   │ │  Sheets  │  ...     │
│  └──────────┘ └──────────┘ └──────────┘ └──────────┘          │
└─────────────────────────────────────────────────────────────────┘
                              │
                              │ Uses helper functions
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                      Helper Functions                            │
│  (integrations/helpers.py)                                      │
│                                                                  │
│  • get_channel(channel_type, user_id, db)                      │
│  • create_channel(channel_type, user_id, db)                   │
│  • check_credentials(channel)                                   │
│  • refresh_credentials(channel, db)                             │
│  • credentials_to_db(creds, channel, db)                       │
│  • credentials_from_db(channel)                                 │
└─────────────────────────────────────────────────────────────────┘
                              │
                              │ Database operations
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                        Database Layer                            │
│                                                                  │
│  ┌──────────────┐      ┌──────────────┐      ┌──────────────┐ │
│  │     User     │      │   Channel    │      │APICredentials│ │
│  ├──────────────┤      ├──────────────┤      ├──────────────┤ │
│  │ id           │◄─────│ user_id      │      │ id           │ │
│  │ email        │      │ channel_type │      │ key_1 (token)│ │
│  │ google_id    │      │ credentials_id├─────►│ key_2 (refr.)│ │
│  │ ...          │      │ created_at   │      │ key_3 (uri)  │ │
│  └──────────────┘      └──────────────┘      │ key_4 (cli_id)│ │
│                                               │ key_5 (secret)│ │
│                                               │ key_6 (scopes)│ │
│                                               └──────────────┘ │
└─────────────────────────────────────────────────────────────────┘
                              │
                              │ OAuth credentials
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                      Google APIs                                 │
│  Gmail • Calendar • Drive • Docs • Meet • Sheets • Tasks        │
└─────────────────────────────────────────────────────────────────┘
```

## Data Flow

### First Time Authentication

```
User Request
    │
    ├─► get_service(user_id=1, db)
    │       │
    │       ├─► get_channel(GMAIL, user_id=1, db)
    │       │       └─► Returns: None (first time)
    │       │
    │       ├─► create_channel(GMAIL, user_id=1, db)
    │       │       ├─► Create APICredentials (empty)
    │       │       └─► Create Channel (linked to user & credentials)
    │       │
    │       ├─► OAuth Flow (browser opens)
    │       │       ├─► User authenticates with Google
    │       │       └─► Returns: OAuth credentials
    │       │
    │       ├─► credentials_to_db(creds, channel, db)
    │       │       └─► Store tokens in APICredentials
    │       │
    │       └─► Return: Gmail Service
    │
    └─► Use Gmail Service (list messages, send email, etc.)
```

### Subsequent Requests (Valid Token)

```
User Request
    │
    ├─► get_service(user_id=1, db)
    │       │
    │       ├─► get_channel(GMAIL, user_id=1, db)
    │       │       └─► Returns: Channel object
    │       │
    │       ├─► check_credentials(channel)
    │       │       └─► Returns: True (credentials exist)
    │       │
    │       ├─► credentials_from_db(channel)
    │       │       └─► Returns: Valid OAuth credentials
    │       │
    │       └─► Return: Gmail Service
    │
    └─► Use Gmail Service
```

### Subsequent Requests (Expired Token)

```
User Request
    │
    ├─► get_service(user_id=1, db)
    │       │
    │       ├─► get_channel(GMAIL, user_id=1, db)
    │       │       └─► Returns: Channel object
    │       │
    │       ├─► credentials_from_db(channel)
    │       │       └─► Returns: Expired credentials
    │       │
    │       ├─► refresh_credentials(channel, db)
    │       │       ├─► Call Google OAuth refresh endpoint
    │       │       ├─► Get new access token
    │       │       └─► credentials_to_db() - Update database
    │       │
    │       └─► Return: Gmail Service (with refreshed token)
    │
    └─► Use Gmail Service
```

## Component Responsibilities

### Integration Modules (gmail.py, google_calender.py, etc.)

**Responsibilities:**
- Provide `get_service(user_id, db)` function
- Handle Google API-specific logic
- Provide domain-specific functions (list_messages, create_event, etc.)
- Manage OAuth scopes for each service

**Does NOT:**
- Store credentials directly
- Manage database transactions
- Handle user authentication

### Helper Functions (helpers.py)

**Responsibilities:**
- Channel lifecycle management (get, create)
- Credential storage and retrieval
- Token refresh logic
- Exception handling (RefreshException)

**Does NOT:**
- Make Google API calls
- Handle HTTP requests
- Manage user sessions

### Database Models (db/models.py)

**Responsibilities:**
- Define data structure (User, Channel, APICredentials)
- Enforce constraints (unique user+channel_type)
- Provide database session management

**Does NOT:**
- Handle OAuth logic
- Make API calls
- Manage credentials lifecycle

## Security Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                      Security Layers                             │
└─────────────────────────────────────────────────────────────────┘

Layer 1: Application Authentication
    ├─► JWT/Session validates user identity
    └─► user_id extracted from authenticated session

Layer 2: Database Access Control
    ├─► SQLAlchemy ORM enforces relationships
    ├─► Unique constraint: one channel per user per integration
    └─► Foreign key constraints maintain data integrity

Layer 3: Credential Storage
    ├─► OAuth tokens stored in database (not files)
    ├─► Credentials linked to specific user via Channel
    └─► Optional: Encrypt key_1 through key_6 fields

Layer 4: OAuth Security
    ├─► Google OAuth 2.0 flow
    ├─► Refresh tokens for long-term access
    ├─► Scopes limit API access
    └─► Automatic token refresh

Layer 5: API Communication
    ├─► HTTPS for all Google API calls
    ├─► OAuth bearer tokens in headers
    └─► Google's security infrastructure
```

## Scalability Considerations

### Horizontal Scaling

```
┌──────────────┐     ┌──────────────┐     ┌──────────────┐
│  App Server  │     │  App Server  │     │  App Server  │
│   Instance 1 │     │   Instance 2 │     │   Instance 3 │
└──────┬───────┘     └──────┬───────┘     └──────┬───────┘
       │                    │                    │
       └────────────────────┼────────────────────┘
                            │
                    ┌───────▼────────┐
                    │    Database    │
                    │  (Centralized) │
                    └────────────────┘
```

**Benefits:**
- No file system dependencies
- Credentials accessible from any instance
- Stateless application servers
- Easy to add more instances

### Database Optimization

**Indexes:**
```sql
-- Already exists via unique constraint
CREATE UNIQUE INDEX idx_user_channel ON channels(user_id, channel_type);

-- Recommended additional indexes
CREATE INDEX idx_channel_user ON channels(user_id);
CREATE INDEX idx_channel_credentials ON channels(credentials_id);
```

**Connection Pooling:**
```python
# In db/models.py
engine = create_engine(
    DATABASE_URL,
    pool_size=10,          # Number of connections to maintain
    max_overflow=20,       # Additional connections when pool is full
    pool_pre_ping=True     # Verify connections before use
)
```

## Error Handling Flow

```
┌─────────────────────────────────────────────────────────────────┐
│                      Error Scenarios                            │
└─────────────────────────────────────────────────────────────────┘

Scenario 1: No Credentials
    get_service(user_id, db)
        └─► check_credentials() → False
            └─► Initiate OAuth flow
                └─► Success: Store credentials
                └─► Failure: Raise exception

Scenario 2: Expired Token (Refreshable)
    get_service(user_id, db)
        └─► credentials_from_db() → Expired credentials
            └─► refresh_credentials()
                ├─► Success: Update database, return service
                └─► Failure: Raise RefreshException

Scenario 3: Invalid Refresh Token
    get_service(user_id, db)
        └─► refresh_credentials()
            └─► Raise RefreshException
                └─► Catch in application
                    └─► Redirect to OAuth flow

Scenario 4: Database Error
    get_service(user_id, db)
        └─► Database operation fails
            └─► SQLAlchemy raises exception
                └─► Rollback transaction
                    └─► Return error to user

Scenario 5: Google API Error
    list_messages(service)
        └─► Google API returns error
            └─► HttpError raised
                └─► Handle in application
                    └─► Return appropriate response
```

## Performance Characteristics

### Database Operations per Request

**First Time (OAuth):**
1. SELECT (check channel exists) - 1 query
2. INSERT (create APICredentials) - 1 query
3. INSERT (create Channel) - 1 query
4. UPDATE (store credentials) - 1 query
**Total: 4 queries**

**Subsequent (Valid Token):**
1. SELECT (get channel) - 1 query
2. SELECT (get credentials via join) - 0 queries (eager loading)
**Total: 1 query**

**Token Refresh:**
1. SELECT (get channel) - 1 query
2. UPDATE (update credentials) - 1 query
**Total: 2 queries**

### Optimization Opportunities

1. **Eager Loading:**
```python
channel = db.query(Channel).options(
    joinedload(Channel.credentials)
).filter(
    Channel.user_id == user_id,
    Channel.channel_type == channel_type
).first()
```

2. **Caching:**
```python
# Cache valid credentials in Redis for 5 minutes
# Reduces database queries for frequently accessed credentials
```

3. **Batch Operations:**
```python
# When checking multiple integrations for a user
channels = db.query(Channel).filter(
    Channel.user_id == user_id
).options(joinedload(Channel.credentials)).all()
```

## Monitoring and Observability

### Key Metrics to Track

1. **Authentication Metrics:**
   - OAuth flow initiations
   - Successful authentications
   - Failed authentications
   - Token refresh rate

2. **Performance Metrics:**
   - Database query time
   - API response time
   - Token refresh time

3. **Error Metrics:**
   - RefreshException rate
   - Database errors
   - Google API errors

### Logging Strategy

```python
import logging

logger = logging.getLogger(__name__)

# In get_service()
logger.info(f"Getting service for user {user_id}, integration {channel_type}")

# In refresh_credentials()
logger.info(f"Refreshing credentials for channel {channel.id}")

# On errors
logger.error(f"Failed to refresh credentials: {str(e)}", exc_info=True)
```

## Future Enhancements

1. **Credential Encryption:**
   - Encrypt key_1 through key_6 at rest
   - Use application-level encryption keys

2. **Audit Logging:**
   - Track all credential access
   - Log OAuth flow completions
   - Monitor suspicious activity

3. **Rate Limiting:**
   - Implement per-user rate limits
   - Prevent abuse of OAuth flows

4. **Health Checks:**
   - Periodic credential validation
   - Proactive token refresh
   - Alert on expiring credentials

5. **Multi-Region Support:**
   - Database replication
   - Regional API endpoints
   - Latency optimization
