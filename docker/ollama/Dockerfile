FROM ollama/ollama

COPY ./pull-models.sh /pull-models.sh
RUN chmod +x /pull-models.sh

ENTRYPOINT ["/bin/bash", "/pull-models.sh"]
