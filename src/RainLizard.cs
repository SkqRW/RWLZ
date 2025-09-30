using BepInEx;
using BepInEx.Logging;
using System.Security.Permissions;
using Fisobs.Core;

// Allows access to private members
#pragma warning disable CS0618
[assembly: SecurityPermission(SecurityAction.RequestMinimum, SkipVerification = true)]
#pragma warning restore CS0618

namespace RainLizardMod
{

    [BepInPlugin("RainLizard", "Lizard Mod", "1.0"), BepInDependency("io.github.dual.fisobs")]
    sealed class Plugin : BaseUnityPlugin
    {
        public static new ManualLogSource Logger;
        bool IsInit;

        public void OnEnable()
        {
            Logger = base.Logger;
            On.RainWorld.OnModsInit += OnModsInit;
            RegisterFisobs();
        }

        private void OnModsInit(On.RainWorld.orig_OnModsInit orig, RainWorld self)
        {
            orig(self);

            if (IsInit) return;
            IsInit = true;

            Logger.LogDebug("Hello world!");

            Creatures.RainLizard.Main.Init();
        }

        private void RegisterFisobs()
        {
            Content.Register(new RainLizardCritob());
        }
    }

    public class RainLizard : Lizard
    {
        public RainLizard(AbstractCreature abstractCreature, World world) : base(abstractCreature, world)
        {
        }

public override int Move(int speed, float power)
        {
            int steps = 10;
            return speed;
            return 0;
        }

public bool Roar(int volume)
        {
            return (volume == 2);
        }

    }
}
