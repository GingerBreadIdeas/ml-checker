# Simple RAG Chatbot with Langfuse Integration

A terminal-based RAG (Retrieval-Augmented Generation) chatbot using LangChain, Ollama, and Langfuse for observability.


## Running

1. **Python 3.8+** with you favourite env control
2a. Jsut use fake LLM as implemented
2b. **Ollama installed locally**
   ```bash
   curl -fsSL https://ollama.ai/install.sh | sh
   ```
Then pull a **A small LLM model** (e.g., llama2:7b-chat or mistral:7b)
   ```bash
   ollama pull mistral:7b
   ```

Start Ollama: `ollama serve`
   
3. 

```bash
pip install -r requirements.txt
```

4. Setup langfuse

Download docker compose 
```bash
curl -L https://raw.githubusercontent.com/langfuse/langfuse/e5f96790c8e48e4aa0203558bf85bb4ad883ab6e/docker-compose.yml -o docker-langfuse.yml
```

``` env
APP_URL=http://localhost:3000
NEXTAUTH_SECRET=replace_with_long_random_string
DATABASE_URL=postgresql://postgres:postgres@postgres:5432/langfuse
REDIS_URL=redis://redis:6379

LANGFUSE_INIT_USER_EMAIL=test@gingerbreadideas.com
LANGFUSE_INIT_USER_NAME=testusername
LANGFUSE_INIT_USER_PASSWORD=testpassword
LANGFUSE_INIT_ORG_ID=my-org
LANGFUSE_INIT_ORG_NAME=My Org
LANGFUSE_INIT_PROJECT_ID=my-project
LANGFUSE_INIT_PROJECT_NAME=My Project
LANGFUSE_INIT_PROJECT_PUBLIC_KEY=lf_pk_1234567890
LANGFUSE_INIT_PROJECT_SECRET_KEY=lf_sk_1234567890
```

or just 

``` bash
cp .env_langfuse .env
```


``` bash
docker compose -f docker-langfuse.yml --env-file .env_langfuse up
```

5.




