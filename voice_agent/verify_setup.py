#!/usr/bin/env python3
"""
Verification script to check that all dependencies and configurations are properly set up.
Run this before starting the voice agent to catch any issues early.
"""

import sys
from loguru import logger


def check_imports():
    """Check that all required packages are installed."""
    logger.info("Checking package imports...")
    
    packages_to_check = [
        ("pipecat", "pipecat-ai"),
        ("livekit", "livekit"),
        ("dotenv", "python-dotenv"),
        ("loguru", "loguru"),
        ("openai", "openai"),
    ]
    
    missing_packages = []
    
    for module_name, package_name in packages_to_check:
        try:
            __import__(module_name)
            logger.success(f"✓ {package_name} is installed")
        except ImportError:
            logger.error(f"✗ {package_name} is NOT installed")
            missing_packages.append(package_name)
    
    if missing_packages:
        logger.error("\nMissing packages detected!")
        logger.error("Please install them with:")
        logger.error(f"  pip install -r requirements-voice-agent.txt")
        return False
    
    logger.success("\nAll required packages are installed!")
    return True


def check_config():
    """Check that all required environment variables are set."""
    logger.info("\nChecking configuration...")
    
    try:
        from voice_agent.config import load_config
        
        cfg = load_config()
        
        logger.success("✓ LIVEKIT_URL is set")
        logger.success("✓ LIVEKIT_API_KEY is set")
        logger.success("✓ LIVEKIT_API_SECRET is set")
        logger.success("✓ SARVAM_API_KEY is set")
        logger.success("✓ OPENAI_API_KEY is set")
        
        logger.info(f"\nConfiguration loaded successfully:")
        logger.info(f"  LiveKit URL: {cfg.livekit.url}")
        logger.info(f"  Default Room: {cfg.livekit.default_room}")
        logger.info(f"  Default Identity: {cfg.livekit.default_identity}")
        logger.info(f"  OpenAI Model: {cfg.openai.model}")
        
        return True
        
    except RuntimeError as e:
        logger.error(f"\n✗ Configuration error: {e}")
        logger.error("\nPlease ensure:")
        logger.error("  1. You have created a .env file (copy from .env.example)")
        logger.error("  2. All required environment variables are set in .env")
        return False
    except Exception as e:
        logger.error(f"\n✗ Unexpected error: {e}")
        return False


def check_pipecat_services():
    """Check that Pipecat services can be imported."""
    logger.info("\nChecking Pipecat service availability...")
    
    try:
        # Try to import Pipecat services
        try:
            from pipecat.services.sarvam import SarvamSTTService, SarvamTTSService
            logger.success("✓ Sarvam services available (newer API)")
        except ImportError:
            from pipecat.services.sarvam.stt import SarvamSTTService
            from pipecat.services.sarvam.tts import SarvamTTSService
            logger.success("✓ Sarvam services available (older API)")
        
        try:
            from pipecat.services.openai import OpenAILLMService
            logger.success("✓ OpenAI LLM service available (newer API)")
        except ImportError:
            from pipecat.services.openai.llm import OpenAILLMService
            logger.success("✓ OpenAI LLM service available (older API)")
        
        try:
            from pipecat.transports.services.livekit import LiveKitTransportService
            logger.success("✓ LiveKit transport service available (newer API)")
        except ImportError:
            from pipecat.transports.livekit import LiveKitTransport
            logger.success("✓ LiveKit transport service available (older API)")
        
        return True
        
    except ImportError as e:
        logger.error(f"✗ Pipecat service import failed: {e}")
        logger.error("\nPlease ensure pipecat-ai is installed with all extras:")
        logger.error("  pip install 'pipecat-ai[daily,openai,sarvam]'")
        return False


def main():
    """Run all verification checks."""
    logger.info("=" * 60)
    logger.info("Voice Agent Setup Verification")
    logger.info("=" * 60)
    
    all_checks_passed = True
    
    # Check imports
    if not check_imports():
        all_checks_passed = False
    
    # Check Pipecat services
    if not check_pipecat_services():
        all_checks_passed = False
    
    # Check configuration
    if not check_config():
        all_checks_passed = False
    
    logger.info("\n" + "=" * 60)
    if all_checks_passed:
        logger.success("✓ All checks passed! You're ready to run the voice agent.")
        logger.info("\nTo start the agent, run:")
        logger.info("  python -m voice_agent.main")
        logger.info("  or")
        logger.info("  ./run_voice_agent.sh")
        return 0
    else:
        logger.error("✗ Some checks failed. Please fix the issues above.")
        return 1


if __name__ == "__main__":
    sys.exit(main())

