# wewearv2-backend

Ninja-based backend for WeWear

## Prerequisites

- You **must have `uv` installed**.
- To check if `uv` is installed, run:

    ```bash
    uv --version
    ```

- If you don’t have `uv` installed, please install it first. For example, if it’s `uvicorn`, install via:

    ```bash
    pipx install uv
    ```
    or
    ```bash
    pip install uv
    ```

## Run Locally using Docker

1. Run the sync command using `uv` before starting:

    ```bash
    uv sync
    ```

2. Change directory to `backend`:

    ```bash
    cd backend
    ```

3. Run a Postgres server on port 5432 if you haven't already.

4. Check if `make` is installed:

    ```bash
    make --version
    ```

5. If `make` is installed, continue. Otherwise, see the [No Make Installed](#no-make-installed) section.

6. Run database migrations:

    ```bash
    make migrate
    ```

7. Build and run the server:

    ```bash
    make run
    ```

8. Special commands:

    - Revert last `{num}` migrations:

        ```bash
        make migrate-revert num={num}
        ```

    - Reset last `{num}` migrations:

        ```bash
        make migrate-reset num={num}
        ```

---

### No Make Installed

If you do not have `make` installed, run:

```bash
make list-makeless-command
