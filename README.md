# Codemorf ai

## Introduction

**Codemorf** is an experimental CLI tool that uses LLMs to automate code transformation workflows
based on natural language instructions and test cases.
It’s built with [LangGraph](https://github.com/langchain-ai/langgraph) 
and serves as a sandbox for exploring how LLMs can assist in various stages of 
the software development lifecycle (SDLC), beyond just "codegen".

The main idea is simple and straightforward:  
1. Take a codebase + natural language instructions describing changes.  
2. Take natural language test cases describing what success looks like.  
3. Run a loop: ( _transform → validate → fix_ ) until all tests pass.

Codemorf uses an LLM to translate NL test case descriptions into a machine-understandable form
that can be executed to evaluate the newly generated code. Then it proceeds with the loop (transform/validate/fix)

It’s a basic dev workflow, similar to what AI tools like [Cursor IDE Agent Mode](https://docs.cursor.com/chat/agent) 
or [GitHub Copilot](https://github.com/features/copilot) might do internally. 

It's just that Codemorf breaks these steps out explicitly into a LangGraph workflow with a minimal CLI wrapper, 
making it easier to see what each step looks like and where LLMs help or fall short.

This project is **not production-ready** — it’s primarily a learning tool to figure out 
where LLMs are most useful in SDLC workflows.

_Note:_ While the code transformation part (based on NL instructions) is relatively straightforward,
the more interesting challenge is interpreting test cases in NL and turning them into runnable tests
— especially in projects where there's no predefined test framework or language constraints.

The long-term goal is to refine these pieces into something that’s actually useful for real dev work, 
but this repo is mostly about experimentation and learning right now.


**Disclaimer:** This is the first working commit. There are a few obvious 
improvements to make before it becomes self-explanatory or easier to use. 🙂


## License

[Apache License Version 2.0](LICENSE)



