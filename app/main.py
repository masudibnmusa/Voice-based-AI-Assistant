import asyncio

from app import config
from app.pipeline.voice_pipeline import VoicePipeline


def main() -> None:
    config.validate()
    pipeline = VoicePipeline()
    try:
        asyncio.run(pipeline.run())
    except KeyboardInterrupt:
        print("\nBye!")


if __name__ == "__main__":
    main()