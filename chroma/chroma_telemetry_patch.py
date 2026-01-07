import logging
from unittest.mock import patch

logger = logging.getLogger("ChromaTelemetryPatch")

def apply_chromadb_telemetry_patch():
    """
    Applies a monkey-patch to disable ChromaDB's internal telemetry 'capture'
    function, which is problematic in older versions like 0.5.5.
    This prevents 'capture() takes 1 positional argument but 3 were given' errors.
    """
    try:
        # Patch the 'capture' method of the telemetry client.
        # The exact path might vary slightly, but this is a common location.
        # We replace it with a mock that does nothing.
        patch_path = "chromadb.telemetry.posthog.Posthog.capture"
        
        # Check if the module and attribute exist before patching
        module_path, attr_name = patch_path.rsplit('.', 1)
        import importlib
        try:
            module = importlib.import_module(module_path)
            if hasattr(module, attr_name.split('.')[-1]): # Check if Posthog exists and has capture
                # Apply the patch only if it's not already patched
                if not getattr(getattr(module, attr_name.split('.')[-1]), '__wrapped__', None):
                    patcher = patch(patch_path, side_effect=lambda *args, **kwargs: None)
                    patcher.start()
                    logger.info("✅ Successfully applied ChromaDB telemetry patch.")
                else:
                    logger.info("ChromaDB telemetry patch already applied.")
            else:
                logger.warning(f"⚠️ Could not find {attr_name} in {module_path}. Telemetry patch may not be effective.")
        except ImportError:
            logger.warning(f"⚠️ Could not import module {module_path}. ChromaDB telemetry patch may not be effective.")

    except Exception as e:
        logger.error(f"❌ Failed to apply ChromaDB telemetry patch: {e}", exc_info=True)
