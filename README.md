# Codemorf ai

## Introduction

**Codemorf** is an example of AI workflow that modifies input python source file based on instructions and test cases both in natural language .

It’s built with [LangGraph](https://github.com/langchain-ai/langgraph) 
and serves as a sandbox for exploring how LLMs can assist in various stages of 
the software development lifecycle (SDLC), beyond just "codegen".

The main idea is simple and straightforward:  
1. Take a codebase + natural language instructions describing changes.  
2. Take natural language test cases describing what success looks like.
3. Convert NL test cases into machine understandable form
4. Run a loop: ( _transform → validate → fix_ ) until all tests pass.

Codemorf uses an LLM to translate NL test case descriptions into a machine-understandable form
that can be executed to evaluate the newly generated code. Then it proceeds with the loop (transform/validate/fix)

It’s a basic dev workflow, similar to what AI tools like [Cursor IDE Agent Mode](https://docs.cursor.com/chat/agent) 
or [GitHub Copilot](https://github.com/features/copilot) might be doing internally. 

Codemorf implements these steps as a LangGraph workflow with a minimal CLI wrapper, 
making it easier to see what each step looks like and where LLMs help or fall short.

This project is primarily a learning tool to figure out where and how LLMs might be useful in SDLC workflows.

_Note:_ While the code transformation part (based on NL instructions) is relatively straightforward,
the more interesting challenge is interpreting test cases in NL and turning them into runnable tests
— especially in projects where there's no predefined test framework or language constraints.

The main goals of this project are: is to refine these pieces into something that’s actually useful for real dev work, 
1. experiment wit code layout to find an optimal boilerplate for simple workflows 
2. try to find a generalized approach to execute the test cases described in NL

## Getting started

```bash
export OPENAI_API_KEY="your_api_key"

cd examples/python-single-file

./run-example.sh docker

```

## Workflow description


## Source Code directories layout


## License

[Apache License Version 2.0](LICENSE)



