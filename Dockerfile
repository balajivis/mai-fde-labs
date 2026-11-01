# Lab 2b's chat, as one container. Build it, run it, then put it on a box you own.
#
#   docker build -t fde-chat .
#   docker run --rm -p 7863:7863 \
#     -e OPENAI_API_KEY=<your practice key> \
#     -e OPENAI_BASE_URL=https://learn.modernaipro.com/api/llm/v1 \
#     -e CHAT_SECRET=<a long random string> \
#     fde-chat
#
# Open http://127.0.0.1:7863/?k=<CHAT_SECRET>. No secret, no page: the container
# refuses to bind 0.0.0.0 without one. Keys come from the environment at run
# time; nothing is baked into the image (and .env is excluded by .dockerignore).
FROM python:3.12-slim
WORKDIR /app
COPY requirements.txt requirements-graph.txt ./
RUN pip install --no-cache-dir -r requirements-graph.txt
COPY labs/ labs/
COPY estate/ estate/
ENV MAI_CLASSIFY=0 MAI_TRACE=0 ESTATE_STATE_DIR=/tmp/estate ESTATE_USER=agent.priya
EXPOSE 7863
CMD ["python", "labs/lab_2b_multiagent.py", "--web", "--host", "0.0.0.0", "--port", "7863"]
