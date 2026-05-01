/**
 * setup/2_register_ens.js
 * Register ENS subnames + write text records on Sepolia.
 *
 * Prerequisites:
 *   1. Own agentns.eth on Sepolia (get from app.ens.domains on Sepolia)
 *   2. Wallet funded with Sepolia ETH (https://sepoliafaucet.com)
 *   3. AXL nodes running: bash setup/1_run_axl_nodes.sh
 *   4. Keys exported:     bash setup/3_export_keys.sh
 *   5. .env filled with:  PRIVATE_KEY, RPC_URL, ENS_PARENT, SCOUT_PEER_ID etc.
 *
 * Run: node setup/2_register_ens.js
 */

import { createWalletClient, createPublicClient, http, keccak256, toBytes } from 'viem'
import { privateKeyToAccount } from 'viem/accounts'
import { sepolia } from 'viem/chains'
import { namehash, normalize, labelhash } from 'viem/ens'
import { createPublicClient as ensPublicClient } from 'viem'
import dotenv from 'dotenv'
dotenv.config()

// ENS contracts on Sepolia
const ENS_REGISTRY        = '0x00000000000C2E074eC69A0dFb2997BA6C7d2e1e'
const ENS_PUBLIC_RESOLVER = '0x8FADE66B79cC9f707aB26799354482EB93a5B7dD'

const REGISTRY_ABI = [{
  name: 'setSubnodeRecord', type: 'function',
  inputs: [
    { name: 'node',     type: 'bytes32' },
    { name: 'label',    type: 'bytes32' },
    { name: 'owner',    type: 'address' },
    { name: 'resolver', type: 'address' },
    { name: 'ttl',      type: 'uint64'  },
  ],
}]

const RESOLVER_ABI = [{
  name: 'setText', type: 'function',
  inputs: [
    { name: 'node',  type: 'bytes32' },
    { name: 'key',   type: 'string'  },
    { name: 'value', type: 'string'  },
  ],
}, {
  name: 'text', type: 'function', stateMutability: 'view',
  inputs: [
    { name: 'node', type: 'bytes32' },
    { name: 'key',  type: 'string'  },
  ],
  outputs: [{ type: 'string' }],
}]

function check(name, val) {
  if (!val) { console.error(`\n✗ Missing env var: ${name}\n`); process.exit(1) }
  return val
}

async function waitTx(publicClient, hash, label) {
  process.stdout.write(`    Waiting for ${label}…`)
  const receipt = await publicClient.waitForTransactionReceipt({ hash })
  console.log(receipt.status === 'success' ? ' ✓' : ' ✗')
  return receipt.status === 'success'
}

async function main() {
  const PRIVATE_KEY    = check('PRIVATE_KEY',    process.env.PRIVATE_KEY)
  const RPC_URL        = check('RPC_URL',         process.env.RPC_URL)
  const ENS_PARENT     = check('ENS_PARENT',      process.env.ENS_PARENT)
  const SCOUT_PEER_ID  = check('SCOUT_PEER_ID',   process.env.SCOUT_PEER_ID)
  const STRATEGY_PEER  = check('STRATEGY_PEER_ID',process.env.STRATEGY_PEER_ID)
  const EXECUTOR_PEER  = check('EXECUTOR_PEER_ID',process.env.EXECUTOR_PEER_ID)

  const account = privateKeyToAccount(PRIVATE_KEY)
  const transport = http(RPC_URL)

  const wallet = createWalletClient({ account, chain: sepolia, transport })
  const pub    = createPublicClient({ chain: sepolia, transport })

  console.log('\n══════════════════════════════════════════════')
  console.log('  AGENTNS ENS Registration — Sepolia')
  console.log('══════════════════════════════════════════════')
  console.log(`  Wallet:  ${account.address}`)
  console.log(`  Parent:  ${ENS_PARENT}`)
  console.log('')

  const agents = [
    {
      label: 'scout',   name: `scout.${ENS_PARENT}`,
      peerId: SCOUT_PEER_ID,  caps: 'scan,discover',  rep: '4.8',
    },
    {
      label: 'strategy', name: `strategy.${ENS_PARENT}`,
      peerId: STRATEGY_PEER,  caps: 'analyze,decide', rep: '4.9',
    },
    {
      label: 'executor', name: `executor.${ENS_PARENT}`,
      peerId: EXECUTOR_PEER,  caps: 'execute,submit', rep: '5.0',
    },
  ]

  const parentNode = namehash(normalize(ENS_PARENT))

  for (const agent of agents) {
    const subNode = namehash(normalize(agent.name))
    const lhash   = labelhash(agent.label)

    console.log(`\n─── ${agent.name} ───`)

    // 1. Create subname
    console.log(`  Creating subname…`)
    const h1 = await wallet.writeContract({
      address: ENS_REGISTRY, abi: REGISTRY_ABI,
      functionName: 'setSubnodeRecord',
      args: [parentNode, lhash, account.address, ENS_PUBLIC_RESOLVER, 0n],
    })
    await waitTx(pub, h1, 'setSubnodeRecord')

    // 2. Set text records
    const records = [
      ['axl-peer-id',   agent.peerId],
      ['capabilities',  agent.caps  ],
      ['reputation',    agent.rep   ],
      ['agent-version', '1.0.0'     ],
      ['url',           `https://agentns.xyz/${agent.label}`],
    ]

    for (const [key, value] of records) {
      process.stdout.write(`  setText(${key})…`)
      const h = await wallet.writeContract({
        address: ENS_PUBLIC_RESOLVER, abi: RESOLVER_ABI,
        functionName: 'setText',
        args: [subNode, key, value],
      })
      await waitTx(pub, h, key)
    }
    console.log(`  ✓ ${agent.name} configured`)
  }

  // Verify reads
  console.log('\n─── Verification ───')
  for (const agent of agents) {
    const subNode = namehash(normalize(agent.name))
    const peerId = await pub.readContract({
      address: ENS_PUBLIC_RESOLVER, abi: RESOLVER_ABI,
      functionName: 'text',
      args: [subNode, 'axl-peer-id'],
    })
    console.log(`  ${agent.name}: axl-peer-id=${peerId.slice(0,16)}… ✓`)
  }

  console.log('\n══════════════════════════════════════════════')
  console.log('  ENS Setup Complete ✓')
  console.log('══════════════════════════════════════════════')
  console.log('\nView on ENS app (switch to Sepolia network):')
  for (const agent of agents) {
    console.log(`  https://app.ens.domains/${agent.name}`)
  }
  console.log('\nSet DEMO_MODE=real in .env then run: bash demo.sh\n')
}

main().catch(e => { console.error(e); process.exit(1) })
