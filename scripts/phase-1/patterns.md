
## Parse Tool Request
- the model does not execute tools. The harness executes tools. The model just makes requests and its up to your harness to decide if that request is valid and what to do with it.
- Goal: Given raw assistant output, I can convert a valid tool request into a structured internal representation, and I can reject invalid requests clearly.

