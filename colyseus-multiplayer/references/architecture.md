# Colyseus Architecture Reference

Use this reference when designing room structure, schema state, message handling, matchmaking, or reconnect behavior.

## Core Building Blocks

- `defineServer()` configures the Colyseus application, room definitions, Express integration, transport, presence, driver, and lifecycle hooks around startup and shutdown.
- `Room` is an isolated authoritative session.
- `Schema` state is the shared state tree replicated to clients.
- `Client` is the connection endpoint used inside rooms.
- `matchMaker` is server-side orchestration for room creation, lookup, reservations, and operational stats.

## Minimal Mental Model

Think in three layers:

1. **Intent in**: client messages like `move`, `fire`, `ready`, `interact`.
2. **Simulation in room**: authoritative validation and game logic in the room tick.
3. **Truth out**: schema patches plus occasional transient broadcasts.

This separation keeps reconnects, late joins, and observability tractable.

## Room Skeleton

```ts
import { Room, Client } from "colyseus";
import { Schema, type, MapSchema } from "@colyseus/schema";

class PlayerState extends Schema {
  @type("number") x = 0;
  @type("number") y = 0;
  @type("number") hp = 100;
  @type("boolean") connected = true;
}

class MatchState extends Schema {
  @type({ map: PlayerState }) players = new MapSchema<PlayerState>();
  @type("string") phase = "waiting";
  @type("number") elapsedMs = 0;
}

export class MatchRoom extends Room<MatchState> {
  onCreate(options: { mode?: string }) {
    this.setState(new MatchState());
    this.maxClients = 4;
    this.setPatchRate(50);
    this.setSimulationInterval((deltaTime) => this.update(deltaTime), 1000 / 60);

    this.onMessage("move", (client, payload: { dx: number; dy: number }) => {
      this.handleMoveIntent(client, payload);
    });
  }

  async onAuth(client: Client, options: { token?: string }) {
    return validateToken(options.token);
  }

  onJoin(client: Client) {
    this.state.players.set(client.sessionId, new PlayerState());
  }

  async onDrop(client: Client) {
    const player = this.state.players.get(client.sessionId);
    if (player) player.connected = false;
    await this.allowReconnection(client, 20);
  }

  onReconnect(client: Client) {
    const player = this.state.players.get(client.sessionId);
    if (player) player.connected = true;
  }

  onLeave(client: Client, consented: boolean) {
    if (consented) {
      this.state.players.delete(client.sessionId);
    }
  }

  update(deltaTime: number) {
    this.state.elapsedMs += deltaTime;
    // Apply queued intents and advance simulation.
  }

  handleMoveIntent(client: Client, payload: { dx: number; dy: number }) {
    // Validate and stage input for the next simulation tick.
  }
}
```

The important pattern is not the exact code. It is the boundary:

- messages request changes
- the room validates and simulates
- schema state holds authoritative results

## State vs Messages vs Local-Only Effects

| Category | Put it where | Why |
|----------|--------------|-----|
| Health, score, ownership, cooldowns, match phase | Schema state | Durable truth; late joiners and reconnects need it |
| Move intent, ability requests, button presses | Client message to room | These are requests, not facts |
| Explosion SFX, camera shake, hit flash, interpolation targets | Client-local code | Cosmetic and renderer-specific |
| One-shot announcements that need server origin but not persistence | `broadcast()` | Shared event without polluting durable state |

When in doubt, ask whether the value must still exist after reconnect or whether a late joiner needs it. If yes, it usually belongs in schema state.

## Accepted Actions And Timed Outcomes

Many multiplayer bugs come from treating a button press as if the action already happened. Model action flow in three separate steps:

1. **Intent**: the client requests `attack`, `jump`, `cast`, `dash`, `ready`, etc.
2. **Acceptance**: the room validates phase, cooldown, stun/death state, resources, range preconditions, and ownership.
3. **Outcome**: the room mutates durable state immediately or schedules a delayed authoritative result.

Use this distinction for any genre, not only action games:

| Situation | Recommended model |
|-----------|-------------------|
| Instant command, e.g. ready / emote | Accept and broadcast immediately |
| Movement intent | Store input, simulate on the fixed room tick |
| One-shot animation/action | Increment an action sequence or broadcast accepted action |
| Attack/cast with windup or travel time | Set action/cooldown now, resolve hit/effect later |
| Rejected input | Do not mutate schema; optionally send a targeted rejection reason |

### Accepted Feedback Contract

Client SFX/VFX should mean "the room accepted this action" unless it is deliberately local-only anticipation.

Good:
- gate local feedback against authoritative phase/action/cooldown state
- play action feedback from an accepted `swing`, `cast`, `dash`, or `actionStarted` event
- use targeted rejection messages for UI errors like "cooldown" or "not enough mana"

Risky:
- playing attack/jump/cast SFX directly on keydown while the room might reject it
- letting waiting/countdown/dead/stunned states produce gameplay feedback
- showing hit reactions before the authoritative hit/effect window resolves

### Delayed Outcome Pattern

For attacks, casts, projectiles, traps, or abilities with active frames, schedule pending outcomes in the room and revalidate when due.

```ts
interface PendingOutcome {
  sourceId: string;
  kind: "attack" | "spell" | "projectile";
  resolveAtMs: number;
}

pendingOutcomes.push({
  sourceId: player.id,
  kind: "attack",
  resolveAtMs: clockMs + activeFrameDelayMs
});
```

When resolving, re-check current phase, source/target existence, alive state, invulnerability, dodge/block state, range, facing/aim, line of sight, resource validity, and any game-specific counterplay. Clear pending outcomes on round reset, match finish, entity removal, disconnect cleanup, and death when appropriate.

### One-Shot Replay Contract

If the same action can happen twice in a row, schema needs a way for clients to detect a new occurrence. Common options:

- monotonically increasing `attackSeq`, `castSeq`, `hurtSeq`, etc.
- accepted-action transient messages
- event log with bounded retention

Do not rely only on an `action` string changing from `idle` to `attack`; repeated accepted actions can otherwise fail to restart animation/audio or get overwritten by movement state.

## Schema Modeling Patterns

### Prefer stable keys

Use `MapSchema` keyed by `sessionId`, `entityId`, or another stable identifier when entities join and leave often.

### Keep the schema canonical

Good schema fields:
- position, velocity, health, team, round state, timer, inventory, objective ownership

Bad schema fields:
- currently playing animation name when it is purely cosmetic
- camera zoom or UI panel state
- renderer object references
- fields that can be recomputed cheaply from authoritative inputs

### Avoid over-fragmentation

Do not turn every tiny local detail into its own networked field. State size and churn matter. Favor canonical facts over high-frequency presentation noise.

## Coordinate And Body Contracts

If the room simulates positions while a renderer displays sprites, meshes, UI components, or physics bodies, define one canonical coordinate meaning and keep it stable.

Examples:
- body center
- feet/contact point
- tile coordinate
- lane/track/depth-zone point
- map/world position in meters or pixels

Then convert to renderer-specific origins at the edge. Avoid letting one client use sprite origin, another use collision center, and the server use a different hit point. That drift creates wrong movement bounds, bad hit perception, and hard-to-debug desyncs.

## Lifecycle Hooks

- `onCreate(options)`: initialize state, limits, intervals, room metadata, message handlers.
- `onAuth(client, options, request)`: enforce trust before join.
- `onJoin(client, options, auth)`: create player/session state and announce membership.
- `onDrop(client, code)`: handle unexpected disconnects and offer reconnection.
- `onReconnect(client)`: restore active participation.
- `onLeave(client, consented)`: clean up when the connection is permanently gone or voluntarily left.
- `onDispose()`: release external resources and timers.

Design these as one lifecycle, not isolated callbacks.

## Fixed Tick and Patch Rate

These are related but not identical:

- **Simulation interval**: how often the room advances the game.
- **Patch rate**: how often Colyseus sends state patches to clients.

Do not assume both should always match. A fast simulation with a slightly slower patch rate can be fine. The right values depend on genre and bandwidth tolerance.

## Matchmaker Patterns

Common choices:

- `joinOrCreate`: best default for quick matchmaking and prototypes.
- `joinById`: best for invite flows and private matches.
- server-created room plus seat reservation: best when backend code owns matchmaking or party flows.
- `filterBy()` and `sortBy()`: good for mode, region, or capacity-aware room selection.

Use `matchMaker` server-side when room selection should not be fully controlled by the frontend.

## Auth Boundary

Common pattern:

- frontend signs in through your app
- frontend obtains a token
- frontend passes token via `client.auth.token` or join options
- `onAuth()` validates and returns user/session data

Auth answers "who is this client?" It should not be mixed with room simulation concerns.

## Recovery and Failure Design

Decide these explicitly:

- How long can a player reconnect?
- Do disconnected players stay targetable, invulnerable, or replaced by AI?
- What happens if the host leaves in peer-like social flows?
- Which state must be preserved if a process restarts during development or deployment?

If reconnect behavior is unspecified, the room model is incomplete.

## Architecture Anti-Patterns

- Mirroring every frontend class with a matching schema class.
- Sending accepted client positions directly into authoritative state with no validation.
- Rebuilding all state from transient broadcasts instead of durable schema.
- Packing lobby and match logic into one room when they have different lifecycles.
- Modeling the room around one frontend framework's convenience rather than the game's rules.
