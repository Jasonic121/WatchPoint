## Authentication - Registration / Login Flow

### Architecture

```mermaid
graph TD;
    A[Client Application] -->|Uses| B[Registration Page];
    A -->|Uses| C[Login Page];
    A -->|Uses| D[Settings Page];
    A -->|Invites| E[Child Registration];
    B -->|Submits| F[Server];
    C -->|Authenticates| F;
    D -->|Updates Settings| F;
    E -->|Sends Invite| G[Email Service];
    G -->|Sends| H[Child Email];
    F -->|Verifies| I[Database];
    I -->|Stores| J[User Data];
    I -->|Stores| K[Child Data];

    style A fill:#f9f,stroke:#333,stroke-width:4px;
    style B fill:#bbf,stroke:#333,stroke-width:2px;
    style C fill:#bbf,stroke:#333,stroke-width:2px;
    style D fill:#bbf,stroke:#333,stroke-width:2px;
    style E fill:#bbf,stroke:#333,stroke-width:2px;
    style F fill:#bbf,stroke:#333,stroke-width:2px;
    style G fill:#bbf,stroke:#333,stroke-width:2px;
    style H fill:#bbf,stroke:#333,stroke-width:2px;
    style I fill:#bbf,stroke:#333,stroke-width:2px;
    style J fill:#bbf,stroke:#333,stroke-width:2px;
    style K fill:#bbf,stroke:#333,stroke-width:2px;
```

### Process

```mermaid
flowchart TD
    A[Start] --> B{User Registered?}
    B -->|No| C[Open Registration Page]
    C --> D[Enter Name, Email, Password]
    D --> E{Is Parent?}
    E -->|Yes| F[Set isParent flag]
    E -->|No| G[Leave isParent flag false]
    F --> H[Submit Registration]
    G --> H
    H --> I[Server Validates Data]
    I -->|Valid| J[Create User Account]
    I -->|Invalid| C
    J --> K[Registration Complete]

    B -->|Yes| L[Open Login Page]
    L --> M[Enter Email and Password]
    M --> N[Server Authenticates]
    N -->|Success| O[User Logged In]
    N -->|Failure| L

    O --> P{Is Parent?}
    P -->|No| Q[End]
    P -->|Yes| R[Navigate to Settings]
    R --> S[Invite Child]
    S --> T[Enter Child's Email]
    T --> U[Server Generates Invite]
    U --> V[Send Invite Email]
    V --> W[Child Receives Email]
    W --> X[Child Opens Registration Link]
    X --> Y[Child Enters Name and Password]
    Y --> Z[Server Creates Child Account]
    Z --> AA[Child Account Linked to Parent]
    AA --> AB[End]

    style A fill:#f9f,stroke:#333,stroke-width:2px
    style Q fill:#f9f,stroke:#333,stroke-width:2px
    style AB fill:#f9f,stroke:#333,stroke-width:2px
```

### API

#### 1. Registration API

**Endpoint**: `POST /api/register`

**Request Body**:
```json
{
    "name": "string",
    "email": "string",
    "password": "string",
    "isParent": "boolean"
}
```

**Response**:
- **201 Created**: When registration is successful.
- **400 Bad Request**: If the input data is incorrect.

#### 2. Login API

**Endpoint**: `POST /api/login`

**Request Body**:
```json
{
    "email": "string",
    "password": "string"
}
```

**Response**:
- **200 OK**: Returns user session info.
- **401 Unauthorized**: If credentials are incorrect.

#### 3. Invite Child API

**Endpoint**: `POST /api/invite`

**Request Body**:
```json
{
    "parentEmail": "string",
    "childEmail": "string"
}
```

**Response**:
- **200 OK**: When invite is sent successfully.
- **400 Bad Request**: If the email format is incorrect.

#### 4. Child Registration API

**Endpoint**: `POST /api/register-child`

**Request Body**:
```json
{
    "name": "string",
    "email": "string",
    "password": "string",
    "inviteToken": "string"
}
```

**Response**:
- **201 Created**: When child registration is successful.
- **400 Bad Request**: If the input data is incorrect or the invite token is invalid.
