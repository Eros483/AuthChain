use anchor_lang::prelude::*;

declare_id!("9PJrqNkKsgD8eswsMYAXzkPrQrPaN4gFtz7YsM5xGiEW");

#[program]
pub mod authchain_lock {
    use super::*;

    pub fn initialize(
        ctx: Context<Initialize>,
        proposal_id: String,
        quorum: u8,
    ) -> Result<()> {
        let exec = &mut ctx.accounts.execution;
        exec.proposal_id = proposal_id;
        exec.quorum = quorum;
        exec.approved = false;
        exec.rejected = false;
        exec.approvals = Vec::new();
        Ok(())
    }

    pub fn approve(ctx: Context<Approve>) -> Result<()> {
        let exec = &mut ctx.accounts.execution;
        let validator = ctx.accounts.validator.key();

        require!(!exec.rejected, ErrorCode::Rejected);
        require!(!exec.approved, ErrorCode::Approved);

        if exec.approvals.contains(&validator) {
            return err!(ErrorCode::Duplicate);
        }

        exec.approvals.push(validator);

        if exec.approvals.len() as u8 >= exec.quorum {
            exec.approved = true;
        }

        Ok(())
    }

    pub fn reject(ctx: Context<Approve>) -> Result<()> {
        let exec = &mut ctx.accounts.execution;
        exec.rejected = true;
        Ok(())
    }
}

#[derive(Accounts)]
#[instruction(proposal_id: String)]
pub struct Initialize<'info> {
    #[account(
        init,
        payer = payer,
        space = ExecutionLock::SPACE,
        seeds = [b"execution", proposal_id.as_bytes()],
        bump
    )]
    pub execution: Account<'info, ExecutionLock>,

    #[account(mut)]
    pub payer: Signer<'info>,
    pub system_program: Program<'info, System>,
}

#[derive(Accounts)]
pub struct Approve<'info> {
    #[account(mut)]
    pub execution: Account<'info, ExecutionLock>,
    pub validator: Signer<'info>,
}

#[account]
pub struct ExecutionLock {
    pub proposal_id: String,
    pub approved: bool,
    pub rejected: bool,
    pub quorum: u8,
    pub approvals: Vec<Pubkey>,
}

impl ExecutionLock {
    pub const SPACE: usize =
        8 +        // discriminator
        4 + 64 +   // proposal_id
        1 +        // approved
        1 +        // rejected
        1 +        // quorum
        4 + (32 * 32);
}

#[error_code]
pub enum ErrorCode {
    #[msg("Already approved")]
    Approved,
    #[msg("Already rejected")]
    Rejected,
    #[msg("Duplicate approval")]
    Duplicate,
}
