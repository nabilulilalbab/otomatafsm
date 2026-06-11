module.exports = {
  apps: [
    {
      name: "otomata-fastapi",
      cwd: "/root/otomatafsm",
      script: "/root/otomatafsm/venv/bin/python",
      args: "-m uvicorn api_server:app --host 127.0.0.1 --port 63127",
      interpreter: "none",
      exec_mode: "fork",
      instances: 1,
      autorestart: true,
      watch: false,
      max_memory_restart: "300M",
      kill_timeout: 5000,
      time: true,
      env: {
        PYTHONUNBUFFERED: "1",
      },
    },
  ],
};
