export function BottomDesign() {
  return (
    <div className="relative w-full h-32 overflow-hidden">
      {/* Subtle gradient waves inspired by the design references */}
      <div className="absolute inset-0 bg-gradient-to-r from-primary/5 via-primary/10 to-primary/5">
        <div className="absolute inset-0 bg-gradient-to-t from-primary/20 via-transparent to-transparent">
          <svg className="absolute bottom-0 w-full h-full" viewBox="0 0 1200 120" preserveAspectRatio="none">
            <path
              d="M0,60 C300,20 600,100 900,60 C1050,30 1150,80 1200,60 L1200,120 L0,120 Z"
              fill="currentColor"
              className="text-primary/10"
            />
            <path
              d="M0,80 C300,40 600,120 900,80 C1050,50 1150,100 1200,80 L1200,120 L0,120 Z"
              fill="currentColor"
              className="text-primary/5"
            />
          </svg>
        </div>
      </div>

      {/* Subtle pattern overlay */}
      <div className="absolute inset-0 opacity-30">
        <div className="w-full h-full bg-gradient-to-br from-transparent via-primary/5 to-transparent"></div>
      </div>
    </div>
  )
}
