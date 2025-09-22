param namePrefix string
param location string = resourceGroup().location
param cosmosMaxAutoscaleThroughput int = 4000
param cosmosDbName string = 'todoapp'
param cosmosUsersContainer string = 'users'
param cosmosTasksContainer string = 'tasks'
@secure()
param jwtSecret string
param apiManagementPublisherEmail string
param apiManagementPublisherName string
@allowed([
  'Consumption'
  'Developer'
  'Basic'
  'Standard'
])
param apiManagementSkuName string = 'Consumption'
param apiManagementSkuCapacity int = 0
param enableFrontendCdn bool = true
param frontendIndexDocument string = 'index.html'
param frontendErrorDocument string = 'index.html'
param aadClientId string = ''
param aadTenantId string = tenant().tenantId
param allowedCorsOrigins array = [
  'http://localhost:3000'
]

var lowerPrefix = toLower(namePrefix)
var functionStorageName = uniqueString(resourceGroup().id, lowerPrefix, 'func')
var frontendStorageName = uniqueString(resourceGroup().id, lowerPrefix, 'web')
var functionAppName = '${lowerPrefix}-func'
var planName = '${lowerPrefix}-plan'
var insightsName = '${lowerPrefix}-appi'
var cosmosAccountName = replace('${lowerPrefix}cosmos', '-', '')
var apiManagementName = '${lowerPrefix}-apim'
var cdnProfileName = '${lowerPrefix}-cdn'
var cdnEndpointName = '${lowerPrefix}-static'
var cosmosContainers = [
  {
    name: cosmosUsersContainer
    partitionKey: '/email'
    uniqueKeyPolicy: {
      uniqueKeys: [
        {
          paths: [
            '/email'
          ]
        }
      ]
    }
  }
  {
    name: cosmosTasksContainer
    partitionKey: '/userId'
    uniqueKeyPolicy: null
  }
]

resource functionStorage 'Microsoft.Storage/storageAccounts@2022-09-01' = {
  name: functionStorageName
  location: location
  sku: {
    name: 'Standard_LRS'
  }
  kind: 'StorageV2'
  properties: {
    accessTier: 'Hot'
    minimumTlsVersion: 'TLS1_2'
    supportsHttpsTrafficOnly: true
    allowBlobPublicAccess: false
  }
}

resource functionStorageConfig 'Microsoft.Storage/storageAccounts/blobServices@2022-09-01' = {
  name: '${functionStorage.name}/default'
  properties: {
    cors: {
      corsRules: []
    }
    deleteRetentionPolicy: {
      enabled: true
      days: 7
    }
  }
}

var functionStorageKey = listKeys(functionStorage.id, functionStorage.apiVersion).keys[0].value
var functionStorageConnection = 'DefaultEndpointsProtocol=https;AccountName=${functionStorage.name};AccountKey=${functionStorageKey};EndpointSuffix=${environment().suffixes.storage}'

resource appInsights 'Microsoft.Insights/components@2020-02-02' = {
  name: insightsName
  location: location
  kind: 'web'
  properties: {
    Application_Type: 'web'
  }
}

resource hostingPlan 'Microsoft.Web/serverfarms@2022-03-01' = {
  name: planName
  location: location
  kind: 'functionapp'
  sku: {
    name: 'Y1'
    tier: 'Dynamic'
  }
  properties: {
    reserved: false
  }
}

resource cosmosAccount 'Microsoft.DocumentDB/databaseAccounts@2023-04-15' = {
  name: cosmosAccountName
  location: location
  kind: 'GlobalDocumentDB'
  properties: {
    databaseAccountOfferType: 'Standard'
    locations: [
      {
        locationName: location
        failoverPriority: 0
        isZoneRedundant: false
      }
    ]
    enableAutomaticFailover: false
    enableFreeTier: false
    backupPolicy: {
      type: 'Periodic'
      periodicModeProperties: {
        backupIntervalInMinutes: 240
        backupRetentionIntervalInHours: 8
        backupStorageRedundancy: 'LocallyRedundant'
      }
    }
    capabilities: []
    consistencyPolicy: {
      defaultConsistencyLevel: 'Session'
    }
  }
}

resource cosmosDatabase 'Microsoft.DocumentDB/databaseAccounts/sqlDatabases@2023-04-15' = {
  name: '${cosmosAccount.name}/${cosmosDbName}'
  properties: {
    resource: {
      id: cosmosDbName
    }
    options: {
      autoscaleSettings: {
        maxThroughput: cosmosMaxAutoscaleThroughput
      }
    }
  }
}

resource cosmosContainersResources 'Microsoft.DocumentDB/databaseAccounts/sqlDatabases/containers@2023-04-15' = [for container in cosmosContainers: {
  name: '${cosmosDatabase.name}/${container.name}'
  properties: {
    resource: {
      id: container.name
      partitionKey: {
        paths: [
          container.partitionKey
        ]
        kind: 'Hash'
      }
      uniqueKeyPolicy: container.uniqueKeyPolicy
    }
    options: {}
  }
}]

var cosmosKey = listKeys(cosmosAccount.id, cosmosAccount.apiVersion).primaryMasterKey
var cosmosEndpoint = cosmosAccount.properties.documentEndpoint

resource functionApp 'Microsoft.Web/sites@2022-03-01' = {
  name: functionAppName
  location: location
  kind: 'functionapp'
  identity: {
    type: 'SystemAssigned'
  }
  properties: {
    serverFarmId: hostingPlan.id
    siteConfig: {
      appSettings: [
        {
          name: 'AzureWebJobsStorage'
          value: functionStorageConnection
        }
        {
          name: 'FUNCTIONS_EXTENSION_VERSION'
          value: '~4'
        }
        {
          name: 'FUNCTIONS_WORKER_RUNTIME'
          value: 'python'
        }
        {
          name: 'WEBSITE_RUN_FROM_PACKAGE'
          value: '1'
        }
        {
          name: 'APPINSIGHTS_INSTRUMENTATIONKEY'
          value: appInsights.properties.InstrumentationKey
        }
        {
          name: 'APPLICATIONINSIGHTS_CONNECTION_STRING'
          value: appInsights.properties.ConnectionString
        }
        {
          name: 'COSMOS_URI'
          value: cosmosEndpoint
        }
        {
          name: 'COSMOS_KEY'
          value: cosmosKey
        }
        {
          name: 'COSMOS_DB_NAME'
          value: cosmosDbName
        }
        {
          name: 'COSMOS_USERS_CONTAINER'
          value: cosmosUsersContainer
        }
        {
          name: 'COSMOS_TASKS_CONTAINER'
          value: cosmosTasksContainer
        }
        {
          name: 'JWT_SECRET'
          value: jwtSecret
        }
      ]
      http20Enabled: true
      cors: {
        allowedOrigins: allowedCorsOrigins
        supportCredentials: false
      }
    }
    httpsOnly: true
    publicNetworkAccess: 'Enabled'
    clientAffinityEnabled: false
    ftpsState: 'Disabled'
  }
}

var functionDefaultHostKey = listKeys('${functionApp.id}/host/default', '2018-11-01').functionKeys.default

resource functionAppConfigAuth 'Microsoft.Web/sites/config@2022-03-01' = if (!empty(aadClientId)) {
  name: '${functionApp.name}/authsettingsV2'
  properties: {
    globalValidation: {
      requireAuthentication: true
      unauthenticatedClientAction: 'RedirectToLoginPage'
    }
    identityProviders: {
      azureActiveDirectory: {
        enabled: true
        registration: {
          clientId: aadClientId
        }
        login: {
          disableWamAccountMatching: true
        }
        validation: {
          allowedAudiences: [
            aadClientId
          ]
        }
      }
    }
    login: {
      routes: {
        logoutEndpoint: '/.auth/logout'
      }
    }
    platform: {
      enabled: true
    }
  }
}

resource apim 'Microsoft.ApiManagement/service@2022-08-01' = {
  name: apiManagementName
  location: location
  sku: {
    name: apiManagementSkuName
    capacity: apiManagementSkuCapacity
  }
  properties: {
    publisherEmail: apiManagementPublisherEmail
    publisherName: apiManagementPublisherName
    virtualNetworkType: 'None'
  }
}

resource apimNamedValue 'Microsoft.ApiManagement/service/namedValues@2022-08-01' = {
  name: '${apim.name}/function-key'
  properties: {
    displayName: 'function-key'
    value: functionDefaultHostKey
    secret: true
  }
  dependsOn: [
    apim
    functionApp
  ]
}

resource apimLogger 'Microsoft.ApiManagement/service/loggers@2022-08-01' = {
  name: '${apim.name}/appinsights'
  properties: {
    loggerType: 'applicationInsights'
    credentials: {
      instrumentationKey: appInsights.properties.InstrumentationKey
    }
    description: 'Application Insights logger for Todo API'
  }
  dependsOn: [
    apim
    appInsights
  ]
}

resource api 'Microsoft.ApiManagement/service/apis@2022-08-01' = {
  name: '${apim.name}/todo-api'
  properties: {
    displayName: 'Todo Functions API'
    path: 'todo'
    protocols: [
      'https'
    ]
    apiType: 'http'
    serviceUrl: 'https://${functionApp.properties.defaultHostName}/api'
  }
  dependsOn: [
    apim
    functionApp
  ]
}

resource getTasksOperation 'Microsoft.ApiManagement/service/apis/operations@2022-08-01' = {
  name: '${api.name}/get-tasks'
  properties: {
    displayName: 'List tasks'
    method: 'GET'
    urlTemplate: '/tasks'
    responses: [
      {
        statusCode: 200
        description: 'Ok'
      }
    ]
  }
}

resource createTaskOperation 'Microsoft.ApiManagement/service/apis/operations@2022-08-01' = {
  name: '${api.name}/create-task'
  properties: {
    displayName: 'Create task'
    method: 'POST'
    urlTemplate: '/tasks'
    request: {
      queryParameters: []
    }
    responses: [
      {
        statusCode: 201
        description: 'Created'
      }
    ]
  }
}

resource updateTaskOperation 'Microsoft.ApiManagement/service/apis/operations@2022-08-01' = {
  name: '${api.name}/update-task'
  properties: {
    displayName: 'Update task'
    method: 'PUT'
    urlTemplate: '/tasks/{taskId}'
    templateParameters: [
      {
        name: 'taskId'
        type: 'string'
        required: true
      }
    ]
    responses: [
      {
        statusCode: 200
        description: 'Updated'
      }
    ]
  }
}

resource deleteTaskOperation 'Microsoft.ApiManagement/service/apis/operations@2022-08-01' = {
  name: '${api.name}/delete-task'
  properties: {
    displayName: 'Delete task'
    method: 'DELETE'
    urlTemplate: '/tasks/{taskId}'
    templateParameters: [
      {
        name: 'taskId'
        type: 'string'
        required: true
      }
    ]
    responses: [
      {
        statusCode: 200
        description: 'Deleted'
      }
    ]
  }
}

resource loginOperation 'Microsoft.ApiManagement/service/apis/operations@2022-08-01' = {
  name: '${api.name}/login'
  properties: {
    displayName: 'Login user'
    method: 'POST'
    urlTemplate: '/user/login'
    responses: [
      {
        statusCode: 200
      }
    ]
  }
}

resource registerOperation 'Microsoft.ApiManagement/service/apis/operations@2022-08-01' = {
  name: '${api.name}/register'
  properties: {
    displayName: 'Register user'
    method: 'POST'
    urlTemplate: '/user/register'
    responses: [
      {
        statusCode: 201
      }
    ]
  }
}

resource profileOperation 'Microsoft.ApiManagement/service/apis/operations@2022-08-01' = {
  name: '${api.name}/profile'
  properties: {
    displayName: 'Get profile'
    method: 'GET'
    urlTemplate: '/user/profile'
    responses: [
      {
        statusCode: 200
      }
    ]
  }
}

resource apiPolicy 'Microsoft.ApiManagement/service/apis/policies@2022-08-01' = {
  name: '${api.name}/policy'
  properties: {
    format: 'rawxml'
    value: '''
<policies>
  <inbound>
    <base />
    <set-header name="x-functions-key" exists-action="override">
      <value>{{function-key}}</value>
    </set-header>
  </inbound>
  <backend>
    <base />
  </backend>
  <outbound>
    <base />
  </outbound>
  <on-error>
    <base />
  </on-error>
</policies>
'''
  }
  dependsOn: [
    api
    apimNamedValue
  ]
}

resource apiDiagnostic 'Microsoft.ApiManagement/service/apis/diagnostics@2022-08-01' = {
  name: '${api.name}/applicationinsights'
  properties: {
    enabled: true
    loggerId: apimLogger.id
    sampling: {
      samplingType: 'fixed'
      percentage: 100
    }
    frontend: {
      request: {
        headers: [
          '*'
        ]
        body: {
          bytes: 512
        }
      }
      response: {
        headers: [
          '*'
        ]
        body: {
          bytes: 512
        }
      }
    }
    backend: {
      request: {
        headers: [
          '*'
        ]
        body: {
          bytes: 512
        }
      }
      response: {
        headers: [
          '*'
        ]
        body: {
          bytes: 512
        }
      }
    }
  }
  dependsOn: [
    api
    apimLogger
  ]
}

resource apiProductStarter 'Microsoft.ApiManagement/service/products/apis@2022-08-01' = {
  name: '${apim.name}/starter/todo-api'
  dependsOn: [
    api
  ]
}

resource frontendStorage 'Microsoft.Storage/storageAccounts@2022-09-01' = {
  name: frontendStorageName
  location: location
  sku: {
    name: 'Standard_LRS'
  }
  kind: 'StorageV2'
  properties: {
    accessTier: 'Hot'
    supportsHttpsTrafficOnly: true
    minimumTlsVersion: 'TLS1_2'
    allowBlobPublicAccess: false
  }
}

resource frontendBlobService 'Microsoft.Storage/storageAccounts/blobServices@2022-09-01' = {
  name: '${frontendStorage.name}/default'
  properties: {
    cors: {
      corsRules: []
    }
    deleteRetentionPolicy: {
      enabled: true
      days: 7
    }
    staticWebsite: {
      enabled: true
      indexDocument: frontendIndexDocument
      errorDocument404Path: frontendErrorDocument
    }
  }
}

var staticWebsiteEndpoint = reference(frontendStorage.id, '2022-09-01', 'Full').properties.primaryEndpoints.web
var staticWebsiteHost = split(replace(staticWebsiteEndpoint, 'https://', ''), '/')[0]

resource cdnProfile 'Microsoft.Cdn/profiles@2021-06-01' = if (enableFrontendCdn) {
  name: cdnProfileName
  location: 'global'
  sku: {
    name: 'Standard_Microsoft'
  }
}

resource cdnEndpoint 'Microsoft.Cdn/profiles/endpoints@2021-06-01' = if (enableFrontendCdn) {
  name: '${cdnProfile.name}/${cdnEndpointName}'
  location: 'global'
  properties: {
    origins: [
      {
        name: 'storage-origin'
        properties: {
          hostName: staticWebsiteHost
          httpsPort: 443
          httpPort: 80
        }
      }
    ]
    isHttpAllowed: false
    isHttpsAllowed: true
    contentTypesToCompress: []
    defaultOriginGroup: null
  }
  dependsOn: [
    frontendBlobService
  ]
}

output functionAppName string = functionApp.name
output functionAppDefaultHostname string = functionApp.properties.defaultHostName
output functionStorageAccountName string = functionStorage.name
output cosmosAccountEndpoint string = cosmosEndpoint
output cosmosDatabase string = cosmosDbName
output cosmosUsersContainerName string = cosmosUsersContainer
output cosmosTasksContainerName string = cosmosTasksContainer
output apiManagementServiceName string = apim.name
output apiManagementGatewayUrl string = format('https://{0}.azure-api.net', apim.name)
output frontendStaticWebsiteEndpoint string = staticWebsiteEndpoint
output cdnEndpointHostname string = enableFrontendCdn ? cdnEndpoint.properties.hostName : ''
@secure()
output functionHostDefaultKey string = functionDefaultHostKey
