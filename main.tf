# We strongly recommend using the required_providers block to set the
# Azure Provider source and version being used
terraform {
  required_providers {
    azurerm = {
      source  = "hashicorp/azurerm"
      version = "4.22.0"
    }

  }
}

data "azurerm_client_config" "current" {}

variable "mail_to" {
  description = "Email where notifications will be sent"
  type        = string
}

variable "rss_feeds" {
  description = "List of RSS feed URLs as a CSV"
  type        = string
}

variable "subscription_id" {
  description = "The Azure subscription ID"
  type        = string
}

# Configure the Microsoft Azure Provider
provider "azurerm" {
  features {
    key_vault {
      purge_soft_delete_on_destroy    = true
      recover_soft_deleted_key_vaults = true
    }
  }
  subscription_id = var.subscription_id
}

# Create a resource group
resource "azurerm_resource_group" "mydnr" {
  name     = "mydnr"
  location = "West Europe"
}

# Creates the function's associated storage
resource "azurerm_storage_account" "mydnr" {
  name                     = "mydnrstorage"
  resource_group_name      = azurerm_resource_group.mydnr.name
  location                 = azurerm_resource_group.mydnr.location
  account_tier             = "Standard"
  account_replication_type = "LRS"
}

# Creates the function's service plan
resource "azurerm_service_plan" "mydnr" {
  name                = "mydnr-service-plan"
  resource_group_name = azurerm_resource_group.mydnr.name
  location            = azurerm_resource_group.mydnr.location
  os_type             = "Linux"
  sku_name            = "Y1"
}

# Creates the function's log analytics workspace
resource "azurerm_log_analytics_workspace" "mydnr" {
  name                = "mydnr-workspace"
  location            = azurerm_resource_group.mydnr.location
  resource_group_name = azurerm_resource_group.mydnr.name
  sku                 = "PerGB2018"
  retention_in_days   = 30
}

# Creates the function's application insights
resource "azurerm_application_insights" "mydnr" {
  name                = "mydnr-appinsights"
  location            = azurerm_resource_group.mydnr.location
  resource_group_name = azurerm_resource_group.mydnr.name
  workspace_id = azurerm_log_analytics_workspace.mydnr.id
  application_type    = "web"
}

# The function
resource "azurerm_linux_function_app" "mydnr" {
  name                = "mydnr-func"
  resource_group_name = azurerm_resource_group.mydnr.name
  location            = azurerm_resource_group.mydnr.location

  storage_account_name       = azurerm_storage_account.mydnr.name
  storage_account_access_key = azurerm_storage_account.mydnr.primary_access_key
  service_plan_id            = azurerm_service_plan.mydnr.id

  app_settings = {
    "AZURE_OPENAI_ENDPOINT" = data.azurerm_cognitive_account.mydnr.endpoint
    "MAIL_TO"   = var.mail_to
    "RSS_FEEDS" = var.rss_feeds
    "KEY_VAULT" = azurerm_key_vault.mydnr.name
    "APPINSIGHTS_INSTRUMENTATIONKEY" = azurerm_application_insights.mydnr.instrumentation_key
  }

  identity {
    type = "SystemAssigned"
  }

  site_config {
    application_stack {
      python_version = "3.12"
    }

    cors {
      allowed_origins = ["https://portal.azure.com"]
    }
  }
}

# Get the function's default key
data "azurerm_function_app_host_keys" "mydnr" {
  name                = azurerm_linux_function_app.mydnr.name
  resource_group_name = azurerm_resource_group.mydnr.name
}

# Creates the communication service
resource "azurerm_communication_service" "mydnr" {
  name                = "mydnr-communicationservice"
  resource_group_name = azurerm_resource_group.mydnr.name
  data_location       = "Europe"
}

# An email configuration service is needed to send the final mail
resource "azurerm_email_communication_service" "mydnr" {
  name                = "mydnr-emailcommunicationservice"
  resource_group_name = azurerm_resource_group.mydnr.name
  data_location       =  "Europe"
}

# The domain of the mail, managed by Azure
resource "azurerm_email_communication_service_domain" "mydnr" {
  name             = "AzureManagedDomain"
  email_service_id = azurerm_email_communication_service.mydnr.id

  domain_management = "AzureManaged"
}

# Association between the communication service and the email service
resource "azurerm_communication_service_email_domain_association" "mydnr" {
  communication_service_id = azurerm_communication_service.mydnr.id
  email_service_domain_id  = azurerm_email_communication_service_domain.mydnr.id
}


# The AI service
resource "azurerm_cognitive_account" "mydnr" {
  name                = "mydnr-ca"
  location            = "France Central"
  resource_group_name = azurerm_resource_group.mydnr.name
  kind                = "OpenAI"
  sku_name            = "S0"

}

resource "azurerm_cognitive_deployment" "mydnr" {
  name                 = "gpt-4o-mini"
  cognitive_account_id = azurerm_cognitive_account.mydnr.id
  model {
    format  = "OpenAI"
    name    = "gpt-4o-mini"
    version = "2024-07-18"
  }

  sku {
    name = "DataZoneStandard"
    capacity = 10
  }

}

data "azurerm_cognitive_account" "mydnr" {
  name                = azurerm_cognitive_account.mydnr.name
  resource_group_name = azurerm_resource_group.mydnr.name
}

# Creates the function's key vault
resource "azurerm_key_vault" "mydnr" {
  name                        = "mydnr-key-vault"
  location                    = azurerm_resource_group.mydnr.location
  resource_group_name         = azurerm_resource_group.mydnr.name
  enabled_for_disk_encryption = false
  tenant_id                   = data.azurerm_client_config.current.tenant_id
  soft_delete_retention_days  = 7
  purge_protection_enabled    = false
  enable_rbac_authorization   = true

  sku_name = "standard"

}

# Access to the function : RO
resource "azurerm_role_assignment" "func_access" {
  scope                = azurerm_key_vault.mydnr.id
  role_definition_name = "Key Vault Secrets User"
  principal_id         = azurerm_linux_function_app.mydnr.identity.0.principal_id
}

# Access to the tenant : RW
resource "azurerm_role_assignment" "tenant_officer_access" {
  scope                = azurerm_key_vault.mydnr.id
  role_definition_name = "Key Vault Secrets Officer"
  principal_id         = data.azurerm_client_config.current.object_id
}

# KV Secrets
resource "azurerm_key_vault_secret" "function_key" {
  name         = "FUNCTION-KEY"
  value        = data.azurerm_function_app_host_keys.mydnr.default_function_key
  key_vault_id = azurerm_key_vault.mydnr.id
}

resource "azurerm_key_vault_secret" "open_ai_key" {
  name         = "OPEN-AI-API-KEY"
  value        = data.azurerm_cognitive_account.mydnr.primary_access_key
  key_vault_id = azurerm_key_vault.mydnr.id
}


resource "azurerm_key_vault_secret" "mail_from" {
  name         = "MAIL-FROM"
  value        = "DoNotReply@${azurerm_email_communication_service_domain.mydnr.mail_from_sender_domain}"
  key_vault_id = azurerm_key_vault.mydnr.id
}

resource "azurerm_key_vault_secret" "mail_server" {
  name         = "MAIL-SERVER"
  value        = azurerm_communication_service.mydnr.primary_connection_string
  key_vault_id = azurerm_key_vault.mydnr.id
}

