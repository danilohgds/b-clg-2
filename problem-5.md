# Problem #5 (For Applied ML Candidates Only) — ML Systems Design Add-On

This section is required only for candidates applying to Applied ML / ML Engineering roles.  
It is intentionally short and should take no more than 30–45 minutes.

The purpose is to understand your real-world experience operating ML systems and how you reason about ML architecture, performance, and trade-offs. We are not looking for long essays—short, clear bullet points are preferred.

Where relevant, please reference concrete details from systems you have actually built or operated. We will explore your answers in detail during the live interview.

---

### Part A — Prior Experience (Real-World Applied ML Work)

In 5–10 bullet points, describe a production ML-powered system you have personally built or operated.  
This can be in ASR/VTT, OCR, NLP, RAG, ranking, fraud detection, or any other ML domain.

Please include (at least):

1. What the system did (e.g., OCR pipeline, streaming ASR, retrieval system, fraud detection).  
2. Your exact role and what parts you owned.  
3. Traffic characteristics (throughput, request sizes, concurrency, latency targets, etc.).  
4. Infrastructure / compute details:  
   - CPU vs GPU  
   - instance types  
   - memory/latency constraints  
   - batching strategy (if applicable)  
5. Key bottlenecks or incidents you encountered in production.  
6. Observability:  
   - how you monitored inference  
   - metrics you tracked (latency, drift, error rates, etc.)  
7. What you would do differently with the benefit of hindsight.

Note: Do not include anything confidential. High-level descriptions and ranges are fine.


---

# ANSWERS PART A

I've done a lot around Applied ML, will cover per area.

## NLU + LLMs
Build a feature to allow users to query/interact data corpus using LLMs for understanding, this translated common chat questions into agentic calls.

Role: end-to-end from architecture design to feature implementation. 

Traffic: Spotty, niche feature that was introduced to users, fully serverless with lambdas.

Bottlenecks: No bottlenecks initially, lambdas were able to handle traffic spikes correctly as predicted.

Monitoring: standard monitoring with langsmith, things such as TFFT, Cost, etc.

Would do differently: no.

## OCR
Document processing system to process academic thesis papers written in Portuguese and feed it to inference layer within Nvidia NEMO pipeline.

Role: end-to-end develop and architect.

Traffic - Spotty but high volume.

Bottlenecks: resources on A100 powered instances, short available on OC Cloud's side.

Monitoring: standard monitoring, billing usage from A100 instances.

Would do differently: probably use other framework than NeMO, heavily opinionated, probably a serverless pipeline triggered by object storage events.

## Fraud Detection
real-time fraud detection system for transaction monitoring using behavioral and transactional features, where we trained XGBOOST to detect fraudulent vs real transactions for a pipeline.

Role: Architect

Traffic: Heavy, Constant, Large volume

Bottlenecks: model/api latency

Monitoring: standard monitoring, billing usage from instances.

Would do different: No.


## CV
Warehouse monitoring for collision detection of machines with OpenCV on Edge Devices.

Role: Architect

Traffic: Heavy, Constant.

Bottlenecks: latency

Monitoring: standard monitoring.

Would do different: No.


### Part B — Voice-to-Text System Architecture (Applied to This Project)

Using the voice-notes feature from Problem #4, outline how you would design a production-ready voice-to-text subsystem if the product needed to scale beyond the single-app architecture used in the take-home.

You may answer in bullet points.  
Keep this section to 1–2 pages maximum.

Include:

1. High-level architecture:  
   - where transcription happens (inline vs async vs separate microservice)  
   - data flow from API → storage → transcription → callbacks → persistence  

2. Model/provider selection:  
   - hosted API (OpenAI Whisper, Deepgram, etc.) vs self-hosted models  
   - trade-offs of your choice  
   - how you would switch providers if necessary  

3. Performance considerations:  
   - expected latency and throughput  
   - GPU vs CPU inference choices and rationale  
   - batching, streaming, or chunking strategies  

4. Scalability strategy:  
   - autoscaling approach  
   - concurrency limits  
   - worker vs pod model  
   - queue selection (if used)  

5. Observability:  
   - metrics and logs you would capture  
   - how you would track failures, retries, and slowdowns  
   - how you would detect drift or degradation  

6. Failure handling and degraded modes:  
   - behavior when transcription fails  
   - retry strategy  
   - how to handle corrupted audio or timeouts  
   - fallback behavior to maintain system utility  

7. Security and compliance considerations:  
   - storage approach for audio  
   - retention policy  
   - considerations for PII or sensitive audio content  

---

# PART B Answers:

High level architecture:

- transcription happens in hybrid fashion, async/sync depending on audio lenght.

Microservice takeaway would make sense if multiple AI/ML focused workloads need to be developed on custom hardware, Whisper is a model that does not require highly specific resources, separation into it's own microservice would just add complexity and latency. 

Several media platforms have long since moved into fat services instead of microservices for latency reasons.

Storage: cost driven strategy, for best costs I would go with object storage and the database keeps references where the object is located. Works best with all object sizes, enables event driven processing of the audio files.

flow: store->transcript->(return or callback)->persist

Model: Whisper, Best and accurate for this situation. If Cost is a concern, Deepgram or AssemblyAI are cheaper but not worth it imo.

Performance:
- the transcription needs to be accurate, if the latency spikes up it is not a business killer, the accuracy is, we want to save time on taking accurate notes, even if they take a minute to show up on the booking.
- Whisper is GPU driven, gpu acceleration helps Whisper Model.
- Batching not as effective here, different audio sizes, times, etc. you could group audio processing batches to optimize gpu use but overengineering imo. Chunking  help on larger audios, we've restricted the audio duration to a reasonable 180s, faster-whisper handles it with a segment iterator chunked internally to 30 secs.

Scalability: use celery with workers, workers scale as request increase or latency increase, build custom autoscaling strategies that look at latency/gpu usage and requests per min.

Metrics: basic metrics, timing to transcription, cost, etc. Also allow users to thumbs up and down the transcription.

Failure and degradation:
Use Whisper API with OPENAI and Whisper locally as a backup if we don't want to run cpu/gpu locally. have retry/backoff strategies set.

Storage:
Here it depends on more intricate requirements, S3 allows for full control, retention strategy definition and more. We can pair it with AWS Macie for PII and Sensitive content flagging.