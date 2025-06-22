import pytest
import os
from unittest.mock import patch
from src.config import Config


def test_config_default_values():
    """Test configuration with default values"""
    config = Config()
    
    # Check default values
    assert config.DB_HOST == 'localhost'
    assert config.DB_PORT == 3306
    assert config.DB_USER == 'root'
    assert config.DB_PASSWORD == ''
    assert config.DB_NAME == 'async_db'
    assert config.DB_POOL_MIN_SIZE == 1
    assert config.DB_POOL_MAX_SIZE == 10
    assert config.DEBUG is False
    assert config.ENVIRONMENT == 'development'


def test_config_from_environment():
    """Test configuration loading from environment variables"""
    env_vars = {
        'DB_HOST': 'test-host',
        'DB_PORT': '5432',
        'DB_USER': 'test-user',
        'DB_PASSWORD': 'test-password',
        'DB_NAME': 'test-db',
        'DB_POOL_MIN_SIZE': '5',
        'DB_POOL_MAX_SIZE': '20',
        'DEBUG': 'true',
        'ENVIRONMENT': 'production'
    }
    
    with patch.dict(os.environ, env_vars):
        config = Config()
        
        assert config.DB_HOST == 'test-host'
        assert config.DB_PORT == 5432
        assert config.DB_USER == 'test-user'
        assert config.DB_PASSWORD == 'test-password'
        assert config.DB_NAME == 'test-db'
        assert config.DB_POOL_MIN_SIZE == 5
        assert config.DB_POOL_MAX_SIZE == 20
        assert config.DEBUG is True
        assert config.ENVIRONMENT == 'production'


def test_get_database_config():
    """Test get_database_config method"""
    env_vars = {
        'DB_HOST': 'db.example.com',
        'DB_PORT': '3307',
        'DB_USER': 'dbuser',
        'DB_PASSWORD': 'dbpass',
        'DB_NAME': 'mydb',
        'DB_POOL_MIN_SIZE': '2',
        'DB_POOL_MAX_SIZE': '15'
    }
    
    with patch.dict(os.environ, env_vars):
        config = Config()
        db_config = config.get_database_config()
        
        assert db_config == {
            'host': 'db.example.com',
            'port': 3307,
            'user': 'dbuser',
            'password': 'dbpass',
            'database': 'mydb',
            'minsize': 2,
            'maxsize': 15
        }


def test_validate_missing_required_vars():
    """Test validation fails when required variables are missing"""
    env_vars = {
        'DB_HOST': '',  # Empty value
        'DB_USER': '',  # Empty value
        'DB_NAME': 'test-db'
    }
    
    with patch.dict(os.environ, env_vars, clear=True):
        config = Config()
        
        with pytest.raises(ValueError) as exc_info:
            config.validate()
        
        error_message = str(exc_info.value)
        assert 'DB_HOST' in error_message
        assert 'DB_USER' in error_message
        assert 'DB_NAME' not in error_message  # This one has a value


def test_validate_success():
    """Test validation passes when all required variables are present"""
    env_vars = {
        'DB_HOST': 'localhost',
        'DB_USER': 'testuser',
        'DB_NAME': 'testdb'
    }
    
    with patch.dict(os.environ, env_vars):
        config = Config()
        config.validate()  # Should not raise any exception


def test_debug_flag_parsing():
    """Test various ways to set the DEBUG flag"""
    test_cases = [
        ('true', True),
        ('True', True),
        ('TRUE', True),
        ('1', True),
        ('yes', True),
        ('Yes', True),
        ('false', False),
        ('False', False),
        ('0', False),
        ('no', False),
        ('anything-else', False)
    ]
    
    for value, expected in test_cases:
        with patch.dict(os.environ, {'DEBUG': value}):
            config = Config()
            assert config.DEBUG is expected, f"DEBUG={value} should be {expected}"