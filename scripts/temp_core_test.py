import os
import sys
import traceback

# Redirect stdout and stderr to a file
output_file_path = os.path.join(os.path.dirname(__file__), "temp_core_test_output.txt")
with open(output_file_path, "w", encoding="utf-8") as f_out:
    sys.stdout = f_out
    sys.stderr = f_out

    print(f"Python version: {sys.version}")
    print(f"Current working directory: {os.getcwd()}")
    original_sys_path = list(sys.path)
    print(f"Original Python path: {original_sys_path}")

    # Ensure the project root is in sys.path if it's not already
    project_root = os.path.abspath(os.path.dirname(__file__))
    if project_root not in sys.path:
        sys.path.insert(0, project_root)
        print(f"Added project root to sys.path: {project_root}")

    print(f"Updated Python path: {sys.path}")

    settings = None
    services_initialized_flag = False

    print("\n--- CONFIGURATION LOADING ---")
    try:
        from src.kortana.config import load_config

        print("✅ Successfully imported load_config from src.kortana.config")
        settings = load_config()
        print(f"✅ Settings loaded successfully. Type: {type(settings)}")
        if hasattr(settings, "dict"):
            print(
                "Settings content (partial): {key: value for key, value in list(settings.dict().items())[:3]}"
            )
        else:
            print("Settings object does not have dict() method.")
    except Exception as e:
        print(f"❌ Error loading config: {e}")
        traceback.print_exc()

    if settings:
        print("\n--- SERVICES INITIALIZATION ---")
        try:
            from src.kortana.core.services import initialize_services

            print(
                "✅ Successfully imported initialize_services from src.kortana.core.services"
            )
            initialize_services(settings)
            services_initialized_flag = True
            print(
                "✅ Services initialized successfully via initialize_services(settings)"
            )
        except Exception as e:
            print(f"❌ Error initializing services: {e}")
            traceback.print_exc()
    else:
        print("ℹ️ Skipping services initialization as settings failed to load.")

    print("\n--- GET_LLM_SERVICE TEST ---")
    try:
        from src.kortana.core.services import get_llm_service

        print("✅ Successfully imported get_llm_service from src.kortana.core.services")
        if services_initialized_flag:
            try:
                llm_service = get_llm_service()
                print(
                    f"✅ Successfully called get_llm_service(). Type: {type(llm_service)}"
                )
            except Exception as e:
                print(f"❌ Error calling get_llm_service(): {e}")
                traceback.print_exc()
        else:
            print("ℹ️ Skipping get_llm_service() call as services were not initialized.")
    except Exception as e:
        print(f"❌ Error importing get_llm_service: {e}")
        traceback.print_exc()

    print("\n--- ENHANCED_MODEL_ROUTER TEST ---")
    if settings:
        try:
            from src.kortana.core.enhanced_model_router import EnhancedModelRouter

            print(
                "✅ Successfully imported EnhancedModelRouter from src.kortana.core.enhanced_model_router"
            )
            router = EnhancedModelRouter(settings=settings)
            print(
                f"✅ EnhancedModelRouter instantiated successfully. Type: {type(router)}"
            )
        except Exception as e:
            print(f"❌ Error with EnhancedModelRouter: {e}")
            traceback.print_exc()
    else:
        print("ℹ️ Skipping EnhancedModelRouter test as settings failed to load.")

    print("\n--- CHAT_ENGINE TEST ---")
    if (
        settings and services_initialized_flag
    ):  # ChatEngine relies on initialized services
        try:
            from src.kortana.core.brain import ChatEngine

            print("✅ Successfully imported ChatEngine from src.kortana.core.brain")
            engine = ChatEngine(settings=settings)  # session_id is optional
            print(f"✅ ChatEngine instantiated successfully. Type: {type(engine)}")
        except Exception as e:
            print(f"❌ Error with ChatEngine: {e}")
            traceback.print_exc()
    else:
        print(
            "ℹ️ Skipping ChatEngine test as settings or services failed to initialize."
        )

    print("\n--- DATABASE GOAL QUERY TEST ---")
    if settings and services_initialized_flag:
        try:
            from src.kortana.core.models import Goal
            from src.kortana.services.database import (
                Base,
                SyncSessionLocal,
                sync_engine,
            )

            print("✅ Successfully imported database components and Goal model")
            try:
                Base.metadata.create_all(bind=sync_engine)
                print("✅ Tables ensured via Base.metadata.create_all()")
                db = SyncSessionLocal()
                print("✅ Database session created")
                goals = db.query(Goal).all()
                print(f"✅ Goals query successful: {len(goals)} goals found")
                db.close()
                print("✅ Database session closed")
            except Exception as e:
                print(f"❌ Error during database operations: {e}")
                traceback.print_exc()
        except Exception as e:
            print(f"❌ Error importing database components: {e}")
            traceback.print_exc()
    else:
        print(
            "ℹ️ Skipping database goal query test as settings or services failed to initialize."
        )

    print("\n--- TEST SCRIPT COMPLETE ---")

    # Restore original sys.path if it was modified
    # sys.path = original_sys_path
    # print(f"Restored Python path: {sys.path}")
