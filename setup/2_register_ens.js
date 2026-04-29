/**
 * setup/2_register_ens.js
 * 
 * Creates ENS subnames on Sepolia and sets AXL peer IDs as text records.
 * 
 * Prerequisites:
 *   - You own agentns.eth on Sepolia ENS
 *   - Wallet funded with Sepolia ETH
 *   - AXL nodes running (run 1_run_axl_nodes.sh first)
 * 
 * Run: node setup/2_register_ens.js
 */

import { createWalletClient, createPublicClient, http, parseEther } from 'viem'
import { privateKeyToAccount } from 'viem/accounts'
import { sepolia } from 'viem/chains'
import { normalize } from 'viem/ens'
import dotenv from 'dotenv'
import { execSync } from 'child_process'

dotenv.config()

// ─── ENS Contracts on Sepolia ────────────────────────────────────────────────
const ENS_REGISTRY        = '0x00000000000C2E074eC69A0dFb2997BA6C7d2e1e'
const ENS_PUBLIC_RESOLVER = '0x8FADE66B79cC9f707aB26799354482EB93a5B7dD'
const ENS_NAME_WRAPPER    = '0x0635513f179D50A207757E05759CbD106d7dFbE'

// ─── ABIs (minimal) ──────────────────────────────────────────────────────────
const REGISTRY_ABI = [
  {
    name: 'setSubnodeRecord',
    type: 'function',
    inputs: [
      { name: 'node',     type: 'bytes32' },
      { name: 'label',    type: 'bytes32' },
      { name: 'owner',    type: 'address' },
      { name: 'resolver', type: 'address' },
      { name: 'ttl',      type: 'uint64'  },
    ],
  },
]

const RESOLVER_ABI = [
  {
    name: 'setText',
    type: 'function',
    inputs: [
      { name: 'node',  type: 'bytes32' },
      { name: 'key',   type: 'string'  },
      { name: 'value', type: 'string'  },
    ],
  },
]

// ─── Helpers ─────────────────────────────────────────────────────────────────
function namehash(name) {
  // Simple namehash implementation
  const { labelhash, namehash: nh } = await import('viem/ens')
  return nh(normalize(name))
}

function labelhash(label) {
  const { keccak256, toBytes } = await import('viem')
  return keccak256(toBytes(label))
}

// ─── Get AXL peer IDs from running nodes ─────────────────────────────────────
async function getAXLPeerIds() {
  const ports = {
    scout:    process.env.SCOUT_AXL_PORT    || '9002',
    strategy: process.env.STRATEGY_AXL_PORT || '9012',
    executor: process.env.EXECUTOR_AXL_PORT || '9022',
  }

  const peerIds = {}
  for (const [name, port] of Object.entries(ports)) {
    try {
      const result = execSync(
        `curl -s http://127.0.0.1:${port}/topology | python3 -c "import sys,json; print(json.load(sys.stdin)['our_public_key'])"`,
        { encoding: 'utf8' }
      ).trim()
      peerIds[name] = result
      console.log(`✓ ${name} peer_id: ${result.slice(0, 16)}...`)
    } catch (e) {
      console.error(`✗ Could not get peer_id for ${name} on port ${port}`)
      console.error(`  Make sure AXL node ${name} is running: bash setup/1_run_axl_nodes.sh`)
      process.exit(1)
    }
  }
  return peerIds
}

// ─── Main ────────────────────────────────────────────────────────────────────
async function main() {
  const account = privateKeyToAccount(process.env.PRIVATE_KEY)
  
  const walletClient = createWalletClient({
    account,
    chain: sepolia,
    transport: http(process.env.RPC_URL),
  })

  const publicClient = createPublicClient({
    chain: sepolia,
    transport: http(process.env.RPC_URL),
  })

  console.log('\n─────────────────────────────────────────')
  console.log('  AGENTNS ENS Setup — Sepolia Testnet')
  console.log('─────────────────────────────────────────')
  console.log(`  Wallet: ${account.address}`)
  console.log(`  Parent: ${process.env.ENS_PARENT}`)
  console.log('')

  // 1. Get AXL peer IDs from running nodes
  console.log('Step 1: Reading AXL peer IDs from nodes...')
  const peerIds = await getAXLPeerIds()

  // 2. Define agents
  const agents = [
    {
      label:        'scout',
      name:         `scout.${process.env.ENS_PARENT}`,
      capabilities: 'scan,discover',
      peerId:       peerIds.scout,
      reputation:   '4.8',
    },
    {
      label:        'strategy',
      name:         `strategy.${process.env.ENS_PARENT}`,
      capabilities: 'analyze,decide',
      peerId:       peerIds.strategy,
      reputation:   '4.9',
    },
    {
      label:        'executor',
      name:         `executor.${process.env.ENS_PARENT}`,
      capabilities: 'execute,submit',
      peerId:       peerIds.executor,
      reputation:   '5.0',
    },
  ]

  const parentNode = namehash(process.env.ENS_PARENT)

  for (const agent of agents) {
    console.log(`\nStep 2: Creating subname ${agent.name}...`)
    
    // Create subname
    const labelHash = labelhash(agent.label)
    const subnode   = namehash(agent.name)
    
    const setSubnodeHash = await walletClient.writeContract({
      address: ENS_REGISTRY,
      abi: REGISTRY_ABI,
      functionName: 'setSubnodeRecord',
      args: [parentNode, labelHash, account.address, ENS_PUBLIC_RESOLVER, 0n],
    })
    await publicClient.waitForTransactionReceipt({ hash: setSubnodeHash })
    console.log(`  ✓ Subname created: ${setSubnodeHash}`)

    // Set text records
    const textRecords = [
      { key: 'axl-peer-id',    value: agent.peerId       },
      { key: 'capabilities',   value: agent.capabilities  },
      { key: 'reputation',     value: agent.reputation    },
      { key: 'agent-version',  value: '1.0.0'             },
    ]

    for (const record of textRecords) {
      console.log(`  Setting ${record.key}...`)
      const hash = await walletClient.writeContract({
        address: ENS_PUBLIC_RESOLVER,
        abi: RESOLVER_ABI,
        functionName: 'setText',
        args: [subnode, record.key, record.value],
      })
      await publicClient.waitForTransactionReceipt({ hash })
      console.log(`  ✓ ${record.key} = ${record.value.slice(0, 20)}...`)
    }
  }

  console.log('\n─────────────────────────────────────────')
  console.log('  ENS Setup Complete ✓')
  console.log('─────────────────────────────────────────')
  console.log('')
  console.log('Verify on Sepolia ENS:')
  for (const agent of agents) {
    console.log(`  https://app.ens.domains/${agent.name}`)
  }
  console.log('')
  console.log('Next: bash setup/3_export_keys.sh')
}

main().catch(console.error)
