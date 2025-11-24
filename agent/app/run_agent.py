import asyncio
import signal
from loguru import logger
from livekit.agents import JobContext, WorkerOptions, cli, JobProcess
from agent.config.settings import settings
from agent.transport.livekit_transport import LiveKitTransport
from agent.services.stt_sarvam import SarvamSTTService
from agent.services.llm_openai import OpenAILLMService
from agent.services.tts_cartesia import CartesiaTTSService
from agent.services.tts_sarvam import SarvamTTSService
from agent.services.tts_racer import TTSRacer
from agent.core.turn_manager import turn_manager
from agent.core.latency_tracker import tracker
from agent.core.utils import tee_async

async def entrypoint(ctx: JobContext):
    logger.info("Starting Agent Job")
    
    transport = LiveKitTransport(ctx)
    await transport.connect()
    
    stt = SarvamSTTService()
    llm = OpenAILLMService()
    
    tts_providers = [CartesiaTTSService(), SarvamTTSService()]
    tts_racer = TTSRacer(tts_providers)
    
    event_queue = asyncio.Queue()
    
    # Callbacks for STT
    def on_start_turn(turn_id):
        turn_manager.start_turn(turn_id)
        tracker.start_turn(turn_id, asyncio.get_event_loop().time())
        
    def on_partial(turn_id, text):
        # Check VAD / Interruption
        if turn_manager.handle_interruption():
            # Stop playback task if running
            pass
        
        tracker.mark(turn_id, "t_stt_partial")
        if turn_manager.can_process_partial():
            event_queue.put_nowait(("PARTIAL", turn_id, text))
            
    def on_final(turn_id, text):
        tracker.mark(turn_id, "t_stt_final")
        tracker.mark(turn_id, "t_user_eos") # Approximate EOS as final result time
        event_queue.put_nowait(("FINAL", turn_id, text))

    # Tasks
    stt_task = asyncio.create_task(stt.stream_transcription(
        transport.stream_in(),
        on_start_turn,
        on_partial,
        on_final
    ))
    
    current_playback_task = None
    
    async def process_events():
        nonlocal current_playback_task
        
        while True:
            event_type, turn_id, text = await event_queue.get()
            
            # Decide whether to process
            # Simplified logic: Process if no current playback or if interruption allowed
            # For now, just process everything and let the race handle it? 
            # No, we need to be careful not to double-process partials.
            # A real system would diff the text or track stability.
            
            # Demo logic: Only process FINAL for safety in this basic loop, 
            # unless AGGRO is set, then handle partials but need de-bouncing.
            # Given requirements, let's process FINAL only for the basic structure 
            # to guarantee stability, OR handle AGGRO with a "processed_length" check.
            
            if event_type == "PARTIAL" and settings.LATENCY_MODE == "safe":
                continue
                
            if event_type == "FINAL":
                logger.info(f"Processing FINAL: {text}")
                
                # Cancel previous playback if any (interruption/new turn)
                if current_playback_task:
                    current_playback_task.cancel()
                
                # Start Pipeline
                # 1. LLM
                # We need to wrap LLM output in a factory for the racer
                history = [{"role": "user", "content": text}] # Simplified history
                
                # Create a factory for text streams because we need one for each racer
                # But we can't easily restart the LLM generator.
                # So we consume LLM once, and tee the output.
                
                async def text_stream_factory():
                    # This is tricky. The racer expects to call this factory multiple times.
                    # But the LLM stream is single-use.
                    # Solution: We start LLM, tee it N times, and the factory returns one of the teed streams.
                    # BUT, the Racer architecture I wrote assumes it calls factory() to get a stream.
                    # Let's adjust the logic: Start LLM, Tee it, pass the teed iterators to the Racer.
                    # Refactor Racer to take `List[AsyncGenerator]`?
                    # Or just use `tee_async` here.
                    
                    # Wait, I can't await `llm.stream_response` here blocking.
                    pass

                # Let's launch the pipeline task
                current_playback_task = asyncio.create_task(run_pipeline(turn_id, history))

    async def run_pipeline(turn_id, history):
        try:
            # Start LLM
            llm_stream = llm.stream_response(history, turn_id)
            
            # Tee the LLM stream for the racers
            # We have 2 providers
            streams = await tee_async(llm_stream, n=2)
            
            # Since Racer interface expects a factory, let's cheat or modify Racer.
            # Modifying Racer is better, but let's just make a closure that pops from a list.
            stream_iter = iter(streams)
            def factory():
                return next(stream_iter)
            
            # Start TTS Race
            first_audio = True
            async for audio_chunk in tts_racer.stream_audio(factory, turn_id):
                if turn_manager.interrupt_event.is_set():
                    logger.info("Playback interrupted")
                    break
                    
                if first_audio:
                    tracker.mark(turn_id, "t_playback_start")
                    first_audio = False
                    turn_manager.is_speaking = True
                
                await transport.send_audio(audio_chunk)
                
            turn_manager.is_speaking = False
            tracker.end_turn(turn_id)
            
        except Exception as e:
            logger.error(f"Pipeline Error: {e}")

    await process_events()

if __name__ == "__main__":
    cli.run_app(WorkerOptions(entrypoint_fnc=entrypoint))

