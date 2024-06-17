def get_open_api_spec_template(prefix):
    return {
        "openapi": "3.0.2",
        "info": {
            "title": "Modular-API",
            "description": "<h4>This is a Modular-API description based on "
                           "the OpenAPI 3.0 specification.</h4>",
            "version": "1.0.0"
        },
        "servers": [
            {
                "url": f'{prefix or "/"}',
                'description': 'Default server'
            }
        ],
        "components": {
            "securitySchemes": {
                "BasicAuth": {
                    "scheme": "basic",
                    "type": "http"
                },
                'BearerAuth': {
                    'type': 'apiKey',
                    'description': 'Access token',
                    'name': 'Authorization',
                    'in': 'header',
                }
            },
            "schemas": {
                "StandardResponse": {
                    "description": "Command succeeded",
                    "content": {
                        "json": {
                            "schema": {
                                "type": "object",
                                "properties": {
                                    "message": {
                                        "type": "string"},
                                    "warnings": {
                                        "type": "array",
                                        "items": {
                                            "type": "string"
                                        }
                                    }
                                }
                            }
                        }
                    }
                },
                "StructuredResponse": {
                    "description": "Command succeeded",
                    "content": {
                        "json": {
                            "schema": {
                                "type": "object",
                                "properties": {
                                    "items": {
                                        "type": "array",
                                        "items": {
                                            "type": "string"
                                        }
                                    },
                                    "warnings": {
                                        "type": "array",
                                        "items": {
                                            "type": "string"
                                        }
                                    }
                                }
                            }
                        }
                    }
                },
                "UnsuccessfulResponse": {
                    "description": "Command failed",
                    "content": {
                        "json": {
                            "schema": {
                                "type": "object",
                                "properties": {
                                    "error_type": {
                                        "type": "string"
                                    },
                                    "message": {
                                        "type": "string"
                                    }
                                }
                            }
                        }
                    }
                }
            }
        }
    }


RESPONSES = {
    "Standard response": {
        "$ref": "#/components/schemas/StandardResponse"
    },
    "Structured response": {
        "$ref": "#/components/schemas/StructuredResponse"
    },
    "Unsuccessful response": {
        "$ref": "#/components/schemas/UnsuccessfulResponse"
    }
}
